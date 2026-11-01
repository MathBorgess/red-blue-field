package main

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"io"
	"log"
	"net/http"
	"net/url"
	"os"
	"os/signal"
	"strings"
	"syscall"
	"time"

	"github.com/spiffe/go-spiffe/v2/svid/jwtsvid"
	"github.com/spiffe/go-spiffe/v2/workloadapi"
)

const (
	defaultWIFURL    = "http://mock-api:8080"
	maxResponseBytes = 16 << 10
)

type config struct {
	operation    string
	ticket       string
	table        string
	targetTenant string
	record       string
	task         string
	audience     string
	wifURL       string
	identityOnly bool
}

type exchangeResponse struct {
	AccessToken string `json:"access_token"`
}

type insertRequest struct {
	TableID        string `json:"table_id"`
	TargetTenantID string `json:"target_tenant_id"`
	RecordPayload  string `json:"record_payload"`
}

func main() {
	log.SetFlags(log.LstdFlags | log.LUTC)
	cfg := readConfig()
	if err := validateConfig(cfg); err != nil {
		log.Fatalf("invalid configuration: %v", err)
	}

	ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer stop()
	if err := run(ctx, cfg); err != nil {
		log.Fatalf("lab request failed: %v", err)
	}
}

func readConfig() config {
	var cfg config
	flag.StringVar(&cfg.operation, "operation", "read", "synthetic action: read or insert")
	flag.StringVar(&cfg.ticket, "ticket", "ticket-alpha", "synthetic ticket ID")
	flag.StringVar(&cfg.table, "table", "orders_table", "synthetic table ID for insert")
	flag.StringVar(&cfg.targetTenant, "target-tenant", "tenant-a", "synthetic target tenant for insert")
	flag.StringVar(&cfg.record, "record", "order-994", "synthetic record ID for insert")
	flag.StringVar(&cfg.task, "task", "", "synthetic task grant ID (defaults by operation)")
	flag.StringVar(&cfg.audience, "audience", "mock-wif", "JWT-SVID audience for the local WIF")
	flag.StringVar(&cfg.wifURL, "wif-url", envOr("WIF_URL", defaultWIFURL), "local mock WIF base URL")
	flag.BoolVar(&cfg.identityOnly, "identity-only", false, "fetch JWT-SVID and report identity without WIF exchange")
	flag.Parse()
	if cfg.task == "" {
		cfg.task = defaultTask(cfg.operation)
	}
	return cfg
}

func defaultTask(operation string) string {
	if operation == "insert" {
		return "task-insert-alpha"
	}
	return "task-alpha"
}

func envOr(name, fallback string) string {
	if value := os.Getenv(name); value != "" {
		return value
	}
	return fallback
}

func validateConfig(cfg config) error {
	if cfg.operation != "read" && cfg.operation != "insert" {
		return errors.New("operation must be read or insert")
	}
	if !validTicket(cfg.ticket) {
		return errors.New("ticket must be ticket-alpha or ticket-beta")
	}
	if err := validateInsertArgs(cfg.table, cfg.targetTenant, cfg.record); err != nil {
		return err
	}
	if len(cfg.task) == 0 || len(cfg.task) > 64 || !simpleIdentifier(cfg.task) {
		return errors.New("task must be a short lowercase identifier")
	}
	if len(cfg.audience) == 0 || len(cfg.audience) > 128 || strings.ContainsAny(cfg.audience, " \t\r\n") {
		return errors.New("audience must be a single nonempty value")
	}
	if err := validateLocalURL(cfg.wifURL); err != nil {
		return fmt.Errorf("wif-url: %w", err)
	}
	return nil
}

func simpleIdentifier(value string) bool {
	for _, r := range value {
		if (r < 'a' || r > 'z') && (r < '0' || r > '9') && r != '-' {
			return false
		}
	}
	return true
}

func validTicket(ticket string) bool {
	return ticket == "ticket-alpha" || ticket == "ticket-beta"
}

func validateInsertArgs(table, targetTenant, record string) error {
	if table != "orders_table" && table != "orders_beta_table" {
		return errors.New("table must be orders_table or orders_beta_table")
	}
	if targetTenant != "tenant-a" && targetTenant != "tenant-b" {
		return errors.New("target-tenant must be tenant-a or tenant-b")
	}
	if record != "order-994" && record != "order-995" {
		return errors.New("record must be order-994 or order-995")
	}
	return nil
}

// The container is intentionally confined to the mock API in its Compose network.
func validateLocalURL(raw string) error {
	u, err := url.Parse(raw)
	if err != nil || u.Scheme != "http" || u.User != nil || u.Hostname() == "" || u.RawQuery != "" || u.Fragment != "" {
		return errors.New("expected a plain local HTTP URL")
	}
	switch u.Hostname() {
	case "mock-api", "localhost", "127.0.0.1", "::1":
	default:
		return errors.New("host is outside the local lab")
	}
	if u.Path != "" && u.Path != "/" {
		return errors.New("WIF URL must be a base URL")
	}
	return nil
}

func run(ctx context.Context, cfg config) error {
	if !cfg.identityOnly {
		if cfg.operation == "insert" {
			log.Printf("request operation=insert task=%s table=%s target_tenant=%s record=%s", cfg.task, cfg.table, cfg.targetTenant, cfg.record)
		} else {
			log.Printf("request operation=read task=%s ticket=%s", cfg.task, cfg.ticket)
		}
	}

	// The host-side model sees neither this SVID nor the exchanged token.
	fetchCtx, cancel := context.WithTimeout(ctx, 15*time.Second)
	defer cancel()
	svid, err := workloadapi.FetchJWTSVID(fetchCtx, jwtsvid.Params{Audience: cfg.audience})
	if err != nil {
		return fmt.Errorf("SPIFFE Workload API did not issue a JWT-SVID: %w", err)
	}
	log.Printf("workload_identity spiffe_id=%s audience=%s expires_at=%s", svid.ID, cfg.audience, svid.Expiry.UTC().Format(time.RFC3339))
	if cfg.identityOnly {
		log.Printf("identity_only complete")
		return nil
	}

	client := localHTTPClient(10 * time.Second)
	accessToken, status, err := exchange(ctx, client, cfg.wifURL, cfg.task, svid.Marshal())
	if err != nil {
		return fmt.Errorf("exchange request: %w", err)
	}
	log.Printf("exchange status=%d", status)
	if status != http.StatusOK {
		return fmt.Errorf("exchange rejected with HTTP %d", status)
	}
	if accessToken == "" {
		return errors.New("exchange returned no access_token")
	}

	if cfg.operation == "insert" {
		status, err = insertRecord(ctx, client, cfg.wifURL, cfg.table, cfg.targetTenant, cfg.record, accessToken)
		if err != nil {
			return fmt.Errorf("record insert request: %w", err)
		}
		log.Printf("record_insert table=%s target_tenant=%s record=%s status=%d", cfg.table, cfg.targetTenant, cfg.record, status)
		if status < http.StatusOK || status >= http.StatusMultipleChoices {
			return fmt.Errorf("record insert rejected with HTTP %d", status)
		}
	} else {
		status, err = readTicket(ctx, client, cfg.wifURL, cfg.ticket, accessToken)
		if err != nil {
			return fmt.Errorf("ticket request: %w", err)
		}
		log.Printf("ticket_read ticket=%s status=%d", cfg.ticket, status)
		if status != http.StatusOK {
			return fmt.Errorf("ticket read rejected with HTTP %d", status)
		}
	}
	return nil
}

func localHTTPClient(timeout time.Duration) *http.Client {
	return &http.Client{
		Timeout: timeout,
		Transport: &http.Transport{
			Proxy: nil,
		},
		CheckRedirect: func(_ *http.Request, _ []*http.Request) error {
			return http.ErrUseLastResponse
		},
	}
}

func exchange(ctx context.Context, client *http.Client, baseURL, task, svid string) (string, int, error) {
	requestBody, err := json.Marshal(map[string]string{"task_id": task})
	if err != nil {
		return "", 0, err
	}
	req, err := http.NewRequestWithContext(ctx, http.MethodPost, strings.TrimRight(baseURL, "/")+"/exchange", bytes.NewReader(requestBody))
	if err != nil {
		return "", 0, err
	}
	req.Header.Set("Authorization", "Bearer "+svid)
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Accept", "application/json")
	resp, err := client.Do(req)
	if err != nil {
		return "", 0, err
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		return "", resp.StatusCode, nil
	}
	var parsed exchangeResponse
	if err := json.NewDecoder(io.LimitReader(resp.Body, maxResponseBytes)).Decode(&parsed); err != nil {
		return "", resp.StatusCode, fmt.Errorf("invalid exchange JSON: %w", err)
	}
	return parsed.AccessToken, resp.StatusCode, nil
}

func readTicket(ctx context.Context, client *http.Client, baseURL, ticket, accessToken string) (int, error) {
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, strings.TrimRight(baseURL, "/")+"/tickets/"+ticket, nil)
	if err != nil {
		return 0, err
	}
	req.Header.Set("Authorization", "Bearer "+accessToken)
	req.Header.Set("Accept", "application/json")
	resp, err := client.Do(req)
	if err != nil {
		return 0, err
	}
	defer resp.Body.Close()
	// No ticket content or bearer tokens enter the process log.
	return resp.StatusCode, nil
}

func insertRecord(ctx context.Context, client *http.Client, baseURL, table, targetTenant, record, accessToken string) (int, error) {
	if err := validateInsertArgs(table, targetTenant, record); err != nil {
		return 0, err
	}
	requestBody, err := json.Marshal(insertRequest{
		TableID:        table,
		TargetTenantID: targetTenant,
		RecordPayload:  recordPayload(record),
	})
	if err != nil {
		return 0, err
	}
	req, err := http.NewRequestWithContext(ctx, http.MethodPost, strings.TrimRight(baseURL, "/")+"/records", bytes.NewReader(requestBody))
	if err != nil {
		return 0, err
	}
	req.Header.Set("Authorization", "Bearer "+accessToken)
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Accept", "application/json")
	resp, err := client.Do(req)
	if err != nil {
		return 0, err
	}
	defer resp.Body.Close()
	// The payload and response body remain outside process logs.
	return resp.StatusCode, nil
}

func recordPayload(record string) string {
	if record == "order-995" {
		return "pedido: 995"
	}
	return "pedido: 994"
}
