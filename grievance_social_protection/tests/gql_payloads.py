gql_mutation_create_ticket = """
mutation createTicket {
  createTicket(input: {
    category: "%s",
    title: "%s",
    resolution: "%s",
    priority: "%s",
    dateOfIncident: "%s",
    channel: "%s",
    flags: "%s",
    clientMutationId: "%s"
  }) {
    clientMutationId
  }
}
"""


gql_mutation_update_ticket = """
mutation updateTicket {
  updateTicket(input: {
    id: "%s",
    category: "%s",
    title: "%s",
    resolution: "%s",
    priority: "%s",
    dateOfIncident: "%s",
    channel: "%s",
    flags: "%s",
    status: %s,
    clientMutationId: "%s"
  }) {
    clientMutationId
  }
}
"""
