package fielddesk.authz_test

import data.fielddesk.authz

read_input := data.fielddesk_test_inputs.read
insert_input := data.fielddesk_test_inputs.insert

test_allow_read if {
    authz.allow with input as read_input
}

test_allow_insert if {
    authz.allow with input as insert_input
}

test_deny_missing_input if {
    not authz.allow with input as {}
}

test_deny_inactive_grant if {
    denied := object.union(read_input, {"grant": object.union(read_input.grant, {"active": false})})
    not authz.allow with input as denied
}

test_deny_wrong_actor if {
    denied := object.union(read_input, {"principal": {"sub": "mallory", "tenant_id": "tenant-a"}})
    not authz.allow with input as denied
}

test_deny_wrong_principal_tenant if {
    denied := object.union(read_input, {"principal": {"sub": "alice", "tenant_id": "tenant-b"}})
    not authz.allow with input as denied
}

test_deny_wrong_workload if {
    denied := object.union(read_input, {"workload": {"spiffe_id": "spiffe://fielddesk.test/rogue"}})
    not authz.allow with input as denied
}

test_deny_wrong_task if {
    denied := object.union(read_input, {"task": {"id": "task-other"}})
    not authz.allow with input as denied
}

test_deny_wrong_action if {
    denied := object.union(read_input, {"action": "record.create"})
    not authz.allow with input as denied
}

test_deny_action_resource_mismatch if {
    denied := object.union(read_input, {
        "action": "record.create",
        "grant": object.union(read_input.grant, {"action": "record.create"}),
    })
    not authz.allow with input as denied
}

test_deny_wrong_resource_type if {
    denied := object.union(read_input, {"resource": {"type": "table", "id": "ticket-alpha", "tenant_id": "tenant-a"}})
    not authz.allow with input as denied
}

test_deny_wrong_resource_id if {
    denied := object.union(read_input, {"resource": {"type": "ticket", "id": "ticket-beta", "tenant_id": "tenant-a"}})
    not authz.allow with input as denied
}

test_deny_wrong_resource_tenant if {
    denied := object.union(read_input, {"resource": {"type": "ticket", "id": "ticket-alpha", "tenant_id": "tenant-b"}})
    not authz.allow with input as denied
}

test_deny_cross_tenant_read if {
    denied := object.union(read_input, {"resource": {"type": "ticket", "id": "ticket-beta", "tenant_id": "tenant-b"}})
    not authz.allow with input as denied
}

test_deny_requested_tenant if {
    denied := object.union(read_input, {"requested_tenant_id": "tenant-b"})
    not authz.allow with input as denied
}

test_deny_cross_tenant_insert if {
    denied := object.union(insert_input, {
        "resource": {"type": "table", "id": "orders_beta_table", "tenant_id": "tenant-b"},
        "requested_tenant_id": "tenant-b",
    })
    not authz.allow with input as denied
}

test_deny_wrong_insert_table if {
    denied := object.union(insert_input, {
        "resource": {"type": "table", "id": "orders_beta_table", "tenant_id": "tenant-a"},
    })
    not authz.allow with input as denied
}

test_deny_missing_actor_rights if {
    denied := object.remove(read_input, ["actor_rights"])
    not authz.allow with input as denied
}

test_deny_empty_actor_rights if {
    denied := object.union(insert_input, {"actor_rights": []})
    not authz.allow with input as denied
}

test_deny_widened_grant_same_tenant_without_actor_right if {
    denied := object.union(insert_input, {
        "resource": {"type": "table", "id": "orders_shadow_table", "tenant_id": "tenant-a"},
        "grant": object.union(insert_input.grant, {"resource_id": "orders_shadow_table"}),
    })
    not authz.allow with input as denied
}

test_deny_partial_rights_across_items if {
    denied := object.union(insert_input, {"actor_rights": [
        {"actor": "alice", "tenant_id": "tenant-a", "action": "record.create",
         "resource_type": "table", "resource_id": "orders_shadow_table"},
        {"actor": "mallory", "tenant_id": "tenant-a", "action": "record.create",
         "resource_type": "table", "resource_id": "orders_table"},
    ]})
    not authz.allow with input as denied
}

test_deny_changed_insert_payload_same_tenant if {
    denied := object.union(insert_input, {"requested_payload": "pedido: 995"})
    not authz.allow with input as denied
}

test_deny_missing_insert_payload if {
    denied := object.remove(insert_input, ["requested_payload"])
    not authz.allow with input as denied
}

test_deny_missing_approved_insert_payload if {
    without_grant := object.remove(insert_input, ["grant"])
    denied := object.union(without_grant, {
        "grant": object.remove(insert_input.grant, ["approved_payload"]),
    })
    not authz.allow with input as denied
}

test_deny_empty_approved_insert_payload if {
    denied := object.union(insert_input, {
        "requested_payload": "",
        "grant": object.union(insert_input.grant, {"approved_payload": ""}),
    })
    not authz.allow with input as denied
}

test_deny_read_with_payload if {
    denied := object.union(read_input, {"requested_payload": "pedido: 994"})
    not authz.allow with input as denied
}

test_deny_read_with_approved_payload if {
    denied := object.union(read_input, {
        "grant": object.union(read_input.grant, {"approved_payload": "pedido: 994"}),
    })
    not authz.allow with input as denied
}

test_deny_empty_actor_and_grant_actor if {
    denied := object.union(read_input, {
        "principal": {"sub": "", "tenant_id": "tenant-a"},
        "grant": object.union(read_input.grant, {"actor": ""}),
    })
    not authz.allow with input as denied
}
