package system.authz_test

import data.system.authz

test_allow_decision_query if {
    authz.allow with input as {"method": "POST", "path": ["v1", "data", "fielddesk", "authz", "allow"]}
}

test_allow_health if {
    authz.allow with input as {"method": "GET", "path": ["health"]}
}

test_deny_policy_update if {
    not authz.allow with input as {"method": "PUT", "path": ["v1", "policies", "authz"]}
}

test_deny_data_update if {
    not authz.allow with input as {"method": "PUT", "path": ["v1", "data", "fielddesk", "authz"]}
}

test_deny_other_decision if {
    not authz.allow with input as {"method": "POST", "path": ["v1", "data", "system", "authz", "allow"]}
}

test_deny_missing_request if {
    not authz.allow with input as {}
}
