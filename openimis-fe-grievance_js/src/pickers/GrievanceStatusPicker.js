import React, { Component } from "react";
import { ConstantBasedPicker } from "@openimis/fe-core";

import { GRIEVANCE_STATUS } from "../constants";

class GrievanceStatusPicker extends Component {

    render() {
        const { readOnly = false} = this.props;
        
        return <ConstantBasedPicker
            module="grievance"
            label="Grievance Status"
            constants={GRIEVANCE_STATUS}
            readOnly={readOnly}
            {...this.props}
        />
    }
}

export default GrievanceStatusPicker;