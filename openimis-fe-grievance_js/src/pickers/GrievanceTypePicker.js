import React, { Component } from "react";
import { ConstantBasedPicker } from "@openimis/fe-core";

import { GRIEVANCE_TYPES } from "../constants";

class GrievanceTypePicker extends Component {

    render() {
        const { readOnly = false } = this.props;
        
        return <ConstantBasedPicker
            module="grievance"
            label="Grievance Type"
            constants={GRIEVANCE_TYPES}
            readOnly={readOnly}
            {...this.props}
        />
    }
}

export default GrievanceTypePicker;