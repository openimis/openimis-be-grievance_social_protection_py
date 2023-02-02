import React, { Component } from "react";
import { connect } from "react-redux";
import { withTheme, withStyles } from "@material-ui/core/styles";
import { formatMessageWithValues, historyPush, formatMessage, withTooltip } from "@openimis/fe-core";
import { fetchGrievance } from "../actions";
import { bindActionCreators } from "redux";
import { injectIntl } from 'react-intl';
import { ProgressOrError, Table } from "@openimis/fe-core";
import {Fab, Paper,} from "@material-ui/core";
import { Add } from "@material-ui/icons";




// const styles = theme => ({ 
//     page: theme.page,
// });

const styles = theme => ({
    paper: theme.paper.paper,
    tableTitle: theme.table.title,
    item: theme.paper.item,
    fullHeight: {
        height: "100%"
    },
});

class Grievancepage extends Component {
    

    state = {
        page: 0,
        pageSize: 10,
        afterCursor: null,
        beforeCursor: null,
    }

    constructor(props) {
        super(props);
        this.rowsPerPageOptions = props.modulesManager.getConf("fe-grievance", "rowsPerPageOptions", [5, 10, 15, 50, 100]);
    }

    componentDidMount() {
        this.query();
    }

    query = () => {
        let prms = [];
        prms.push(`first: ${this.state.pageSize}`);
        if (!!this.state.afterCursor) {
            prms.push(`after: "${this.state.afterCursor}"`)
        }
        if (!!this.state.beforeCursor) {
            prms.push(`before: "${this.state.beforeCursor}"`)
        }
        prms.push(`orderBy: ["grievanceCode"]`);
        this.props.fetchGrievance(prms);
    }

    onChangeRowsPerPage = (cnt) => {
        this.setState(
            {
                pageSize: cnt,
                page: 0,
                afterCursor: null,
                beforeCursor: null,
            },
            e =>this.query()
        )
    }

    onChangePage = (page, nbr) => {
        if (nbr > this.state.page) {
            this.setState((state, props) => ({
                page: state.page + 1,
                beforeCursor: null,
                afterCursor: props.grievancePageInfo.endCursor,
            }),
                e => this.query()
            )
        } else if (nbr < this.state.page) {
            this.setState((state, props) => ({
                page: state.page - 1,
                beforeCursor: props.grievancePageInfo.startCursor,
                afterCursor: null,
            }),
                e => this.query()
            )
        }
    }

    onAdd = () => {
        historyPush(this.props.modulesManager, this.props.history, "grievance.route.add_grievance");
    }

    render() {
        const { intl, classes, fetchingGrievance, errorGrievance, Grievance, grievancePageInfo } = this.props;

        let headers = [ 
            // "grievance.code",
            "grievance.type",
            "grievance.beneficiary",
            "grievance.description",
            // "grievance.createdBy",
            "grievance.status",
        ]

        let itemFormatters = [
            // e => e.grievanceCode,
            e => e.typeOfGrievance,
            e => e.insuree.otherNames + ' ' + e.insuree.lastName,
            e => e.description,
            // e => e.createdBy,
            e => e.status,
        ]

        return(
            <div className={classes.page}>
                <ProgressOrError progress={fetchingGrievance} error={errorGrievance} />
                    <Paper className={classes.paper}>      
                        <Table
                            module="grievance"
                            header={formatMessageWithValues(intl, "Grievance", "Grievance.Table", {count: grievancePageInfo.totalCount})}
                            headers={headers}
                            itemFormatters={itemFormatters}
                            items={Grievance}
                            withPagination={true}
                            page={this.state.page}
                            pageSize={this.state.pageSize}
                            count={grievancePageInfo.totalCount}
                            onChangePage={this.onChangePage}
                            onChangeRowsPerPage={this.onChangeRowsPerPage}
                            rowsPerPageOptions={this.rowsPerPageOptions}
                        />
                        
                    </Paper> 
                    {withTooltip(
                            <div align="right" className={classes.fab}>
                                <Fab color="primary"
                                    onClick={this.onAdd}>
                                        <Add />
                                    </Fab>
                            </div>,
                            formatMessage(intl, "grievance", "addNewGrievanceTooltip")
                        )
                        }
            </div>
        )
    }
}

const mapStateToProps = state => ({
    fetchingGrievance: state.grievance.fetchingGrievance,
    errorGrievance: state.grievance.errorGrievance,
    fetchedGrievance: state.grievance.fetchedGrievance,
    Grievance: state.grievance.Grievance,
    grievancePageInfo: state.grievance.grievancePageInfo,
});

const mapDispatchToProps = dispatch => {
    return bindActionCreators({ fetchGrievance }, dispatch)
}
export default injectIntl(withTheme(withStyles(styles)(connect(mapStateToProps, mapDispatchToProps)(Grievancepage))));