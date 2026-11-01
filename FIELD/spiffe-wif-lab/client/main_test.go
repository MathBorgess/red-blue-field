package main

import (
	"context"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"sync/atomic"
	"testing"
	"time"
)

func TestDefaultTaskByOperation(t *testing.T) {
	if got := defaultTask("read"); got != "task-alpha" {
		t.Fatalf("read task = %q", got)
	}
	if got := defaultTask("insert"); got != "task-insert-alpha" {
		t.Fatalf("insert task = %q", got)
	}
}

func TestInsertAllowlist(t *testing.T) {
	if err := validateInsertArgs("orders_table", "tenant-a", "order-994"); err != nil {
		t.Fatal(err)
	}
	for _, args := range [][3]string{
		{"orders_internal", "tenant-a", "order-994"},
		{"orders_table", "tenant-c", "order-994"},
		{"orders_table", "tenant-a", "order-996"},
	} {
		if err := validateInsertArgs(args[0], args[1], args[2]); err == nil {
			t.Fatalf("unexpected acceptance of %v", args)
		}
	}
}

func TestValidateLocalURL(t *testing.T) {
	tests := []struct {
		name string
		url  string
		ok   bool
	}{
		{"mock WIF", "http://mock-api:8080", true},
		{"external host", "http://example.com/exchange", false},
		{"host model", "http://host.docker.internal:11434", false},
		{"userinfo", "http://user@mock-api:8080", false},
		{"unexpected WIF path", "http://localhost:8080/admin", false},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if got := validateLocalURL(tt.url) == nil; got != tt.ok {
				t.Fatalf("validateLocalURL(%q) success = %v, want %v", tt.url, got, tt.ok)
			}
		})
	}
}

func TestExchangeDoesNotForwardSVIDOnRedirect(t *testing.T) {
	var redirected atomic.Bool
	destination := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		redirected.Store(true)
		w.WriteHeader(http.StatusOK)
	}))
	defer destination.Close()

	source := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		http.Redirect(w, r, destination.URL, http.StatusFound)
	}))
	defer source.Close()

	_, status, err := exchange(context.Background(), localHTTPClient(time.Second), source.URL, "task-alpha", "synthetic-svid")
	if err != nil {
		t.Fatal(err)
	}
	if status != http.StatusFound || redirected.Load() {
		t.Fatalf("status = %d, redirected = %v; want 302 and no redirect", status, redirected.Load())
	}
}

func TestInsertRecordMapsAllowlistedPayload(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost || r.URL.Path != "/records" {
			t.Errorf("request = %s %s", r.Method, r.URL.Path)
		}
		if r.Header.Get("Authorization") != "Bearer synthetic-task-token" {
			t.Error("missing task bearer token")
		}
		var body insertRequest
		if err := json.NewDecoder(r.Body).Decode(&body); err != nil {
			t.Error(err)
		}
		if body.TableID != "orders_beta_table" || body.TargetTenantID != "tenant-b" || body.RecordPayload != "pedido: 995" {
			t.Error("unexpected insert body")
		}
		w.WriteHeader(http.StatusCreated)
		_, _ = w.Write([]byte(`{"canary":"must-not-be-logged"}`))
	}))
	defer server.Close()

	status, err := insertRecord(context.Background(), localHTTPClient(time.Second), server.URL,
		"orders_beta_table", "tenant-b", "order-995", "synthetic-task-token")
	if err != nil || status != http.StatusCreated {
		t.Fatalf("insert returned status=%d err=%v", status, err)
	}
	if _, err := insertRecord(context.Background(), localHTTPClient(time.Second), server.URL,
		"orders_table", "tenant-a", "order-996", "synthetic-task-token"); err == nil {
		t.Fatal("unknown record reached HTTP boundary")
	}
}

func TestInsertRecordDoesNotForwardTaskTokenOnRedirect(t *testing.T) {
	var redirected atomic.Bool
	destination := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		redirected.Store(true)
		w.WriteHeader(http.StatusOK)
	}))
	defer destination.Close()
	source := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		http.Redirect(w, r, destination.URL, http.StatusTemporaryRedirect)
	}))
	defer source.Close()

	status, err := insertRecord(context.Background(), localHTTPClient(time.Second), source.URL,
		"orders_table", "tenant-a", "order-994", "synthetic-task-token")
	if err != nil || status != http.StatusTemporaryRedirect || redirected.Load() {
		t.Fatalf("status=%d err=%v redirected=%v", status, err, redirected.Load())
	}
}
