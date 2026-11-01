package fielddesk.authz

# The broker supplies verified identity, its own grant and resource facts.
# No model text or caller-supplied claims may become authoritative here.
default allow := false

valid_action_resource if {
    input.action == "ticket.read"
    input.resource.type == "ticket"
}

valid_action_resource if {
    input.action == "record.create"
    input.resource.type == "table"
}

actor_has_right if {
    is_array(input.actor_rights)
    some right in input.actor_rights
    right.actor == input.principal.sub
    right.tenant_id == input.principal.tenant_id
    right.tenant_id == input.resource.tenant_id
    right.action == input.action
    right.resource_type == input.resource.type
    right.resource_id == input.resource.id
}

valid_payload if {
    input.action == "ticket.read"
    input.requested_payload == null
    input.grant.approved_payload == null
}

valid_payload if {
    input.action == "record.create"
    is_string(input.grant.approved_payload)
    input.grant.approved_payload != ""
    input.requested_payload == input.grant.approved_payload
}

allow if {
    valid_action_resource
    actor_has_right
    valid_payload
    input.grant.active == true

    input.principal.sub != ""
    input.principal.sub == input.grant.actor
    input.principal.tenant_id != ""
    input.principal.tenant_id == input.grant.tenant_id

    input.workload.spiffe_id == "spiffe://fielddesk.test/agent"
    input.workload.spiffe_id == input.grant.workload_id

    input.task.id != ""
    input.task.id == input.grant.task_id

    input.action == input.grant.action
    input.resource.type == input.grant.resource_type
    input.resource.id != ""
    input.resource.id == input.grant.resource_id
    input.resource.tenant_id == input.grant.tenant_id
    input.requested_tenant_id == input.grant.tenant_id
}
