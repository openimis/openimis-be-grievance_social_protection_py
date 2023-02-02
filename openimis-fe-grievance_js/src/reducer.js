import {
    parseData, formatGraphQLError, formatServerError, pageInfo
} from '@openimis/fe-core';

function reducer(
    state = {
        fetchingGrievance: false,
        errorGrievance: null,
        fetchedGrievance: false,
        Grievance: [],
        grievancePageInfo: { totalCount: 0 },
    },
    action,
) {
    switch (action.type) {
        case "GRIEVANCE_MY_GRIEVANCES_REQ":
            return {
                ...state,
                fetchingGrievance: true,
                fetchedGrievance: false,
                Grievance: null,
                grievancePageInfo: { totalCount: 0 },
                errorGrievance: null,
            };
            case 'GRIEVANCE_MY_GRIEVANCES_RESP':
                return {
                    ...state,
                    fetchingGrievance: false,
                    fetchedGrievance: true,
                    Grievance: parseData(action.payload.data.grievance),
                    grievancePageInfo: pageInfo(action.payload.data.grievance),
                    errorGrievance: formatGraphQLError(action.payload)
                };
            case 'GRIEVANCE_MY_GRIEVANCES_ERR':
                return {
                    ...state,
                    fetching: false,
                    error: formatServerError(action.payload)
                };
        default:
            return state;
    }
}

export default reducer;