import React, { Component } from "react";
import { withTheme, withStyles } from "@material-ui/core/styles";
import { Fab, Grid, Paper, Divider, Typography} from "@material-ui/core";
import { TextInput, FormattedMessage, PublishedComponent, historyPush } from "@openimis/fe-core";
import { saveGrievance } from "../actions";
import { connect } from "react-redux";
import { bindActionCreators } from "redux";
import { Save, ArrowBackIos } from "@material-ui/icons";
import { TextField } from '@mui/material';



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


class AddGrievance extends Component {

    state = {
        edited: {}
    }

    save = e => {
        this.props.saveGrievance(this.state.edited, `Creating Grievance ${this.state.edited.grievanceCode}`)
        
    }

    back = e => {
        historyPush(this.props.modulesManager, this.props.history, "grievance.route.my_grievance")
    }

    updateAttribute = (k, v) => {
        this.setState((state) => ({
            edited: { ...state.edited, [k]: v } 
        }))
    }


    render() {
        const { classes, title = "Grievances.title", titleParams = { label: "" }, } = this.props;
        const { edited } = this.state;
        
        return (
            <div className={classes.page}>
                <Grid container>
                    <Grid item xs={12}>
                        <Paper className={classes.paper}>
                        <Grid container className={classes.tableTitle}>
                            <Grid item xs={3} className={classes.tableTitle}>
                                <Typography>
                                    <Fab color="primary" onClick={this.back}>
                                        <ArrowBackIos />
                                    </Fab>
                                    <FormattedMessage module="grievance" id={title} values={titleParams} />
                                </Typography>
                            </Grid>
                        </Grid>
                        <Divider />
                        <Grid container className={classes.item}>
                            <Grid item xs={4} className={classes.item}>
                                <PublishedComponent
                                    pubRef="insuree.InsureePicker"
                                    value={edited.insuree}
                                    onChange={(v) => this.updateAttribute("insuree", v)}
                                    required={true}
                                />
                            </Grid>
                            <Grid item xs={4} className={classes.item}>
                                <PublishedComponent
                                    pubRef="grievance.GrievanceTypePicker"
                                    value={edited.typeOfGrievance}
                                    onChange={(v) => this.updateAttribute("typeOfGrievance", v)}
                                    required={true}
                                />
                            </Grid>
                            <Grid item xs={4} className={classes.item}>
                                <PublishedComponent
                                    pubRef="grievance.GrievanceStatusPicker"
                                    value={edited.status}
                                    onChange={(v) => this.updateAttribute("status", v)}
                                    required={true}
                                />
                            </Grid>
                            {/* <Grid item xs={6} className={classes.item}>
                                <TextInput
                                    module="grievance" label="Grievance.createdBy"
                                    value={edited.createdBy}
                                    required={true}
                                    readOnly={true}
                                    onChange={v => this.updateAttribute("createdBy", v)}
                                />
                            </Grid> */}
                            <Grid item xs={12} className={classes.item}>
                                <TextInput
                                    module="grievance" label="Grievance.description"
                                    value={edited.description}
                                    required={true}
                                    onChange={v => this.updateAttribute("description", v)}
                                />
                            </Grid>
                            {/* <Grid item xs={12} className={classes.item}>
                                <textarea rows="6" cols="80"
                                    module="grievance" label="Grievance.description"
                                    value={edited.description}
                                    required={true}
                                    onChange={v => this.updateAttribute("description", v)}
                                />
                            </Grid> */}
                        </Grid>
                        {/* <Button onClick={this.save}>SAVE</Button> */}
                        <Fab color="primary" onClick={this.save}>
						    <Save />
					    </Fab>
                        </Paper>
                    </Grid>
                </Grid>
                <br/>
            </div>
        )
    }
}

const mapDispatchToProps = dispatch => {
    return bindActionCreators({ saveGrievance }, dispatch);
};

export default withTheme(withStyles(styles)(connect(null, mapDispatchToProps)(AddGrievance)));