package main

import (
	"context"
	"net/http"
	"net/http/httptest"
	"sync/atomic"
	"testing"
	"time"
)

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
