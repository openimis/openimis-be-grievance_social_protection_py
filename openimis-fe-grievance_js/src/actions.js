import {
    graphql, formatPageQueryWithCount, formatMutation
    } from "@openimis/fe-core";

export function fetchGrievance(prms){
    const payload = formatPageQueryWithCount( 
        "grievance",
        prms,
        ["grievanceCode", "typeOfGrievance", "status", "comments", "createdBy", "description", "insuree{otherNames, lastName}"]
    );
    return graphql(payload, 'GRIEVANCE_MY_GRIEVANCES');
}

export function saveGrievance(grievance, clientMutationLabel) {
    let grievanceGQL = ` 
    grievanceCode: "${grievance.grievanceCode}"
    insureeUuid: "${grievance["insuree"]["uuid"]}"
    typeOfGrievance: "${grievance.typeOfGrievance}"
    description: "${grievance.description}"
    createdBy: "${grievance.createdBy}"
    comments: "${grievance.comments}"
    status: "${grievance.status}"
    `
    let mutation = formatMutation("createGrievance", grievanceGQL, clientMutationLabel);
    var requestedDateTime = new Date();
    return graphql(
        mutation.payload,
        "GRIEVANCES_CREATE_GRIEVANCE",
        {
            clientMutationId: mutation.clientMutationId,
            clientMutationLabel,
            requestedDateTime
        }
    )
}