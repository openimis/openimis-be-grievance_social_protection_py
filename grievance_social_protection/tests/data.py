service_add_ticket_payload = {
    "category": "Default",
    "title": "Test",
    "resolution": "8,7",
    "priority": "High",
    "dateOfIncident": "2024-11-20",
    "channel": "Channel A",
    "flags": "Default",
}


service_add_ticket_payload_bad_resolution = {
    "category": "Default",
    "title": "Test",
    "resolution": "sdasdasadsda",
    "priority": "High",
    "dateOfIncident": "2024-11-20",
    "channel": "Channel A",
    "flags": "Default",
}


service_add_ticket_payload_bad_resolution_day = {
    "category": "Default",
    "title": "Test",
    "resolution": "100,5",
    "priority": "High",
    "dateOfIncident": "2024-11-20",
    "channel": "Channel A",
    "flags": "Default",
}


service_add_ticket_payload_bad_resolution_hour = {
    "category": "Default",
    "title": "Test",
    "resolution": "1,54",
    "priority": "High",
    "dateOfIncident": "2024-11-20",
    "channel": "Channel A",
    "flags": "Default",
}


service_update_ticket_payload = {
    "category": "Default",
    "title": "TestUpdate",
    "status": "OPEN",
    "resolution": "1,4",
    "priority": "Medium",
    "dateOfIncident": "2024-11-20",
    "channel": "Channel A",
    "flags": "Default",
}
