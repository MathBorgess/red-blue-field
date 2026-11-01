package system.authz

# The OPA HTTP API has policy/data write endpoints. This local sidecar only
# serves the one decision needed by the broker and a health probe.
default allow := false

allow if {
    input.method == "POST"
    input.path == ["v1", "data", "fielddesk", "authz", "allow"]
}

allow if {
    input.method == "GET"
    input.path == ["health"]
}
