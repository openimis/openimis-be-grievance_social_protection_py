import React,{ Component } from "react";
import { injectIntl } from 'react-intl';
import { ScreenShare } from "@material-ui/icons";
import { formatMessage, MainMenuContribution, withModulesManager } from "@openimis/fe-core";


class GrievanceMainMenu extends Component {
    render() {
        const { intl } = this.props;
        let entries = [];

        if (!entries.length) return null;
        return (
            <MainMenuContribution
                {...this.props}
                header= {formatMessage(intl, "grievance", "mainMenu")}
                icon={<ScreenShare />}
                entries={entries}
            />
        );
    }
}

export default withModulesManager(injectIntl(GrievanceMainMenu));