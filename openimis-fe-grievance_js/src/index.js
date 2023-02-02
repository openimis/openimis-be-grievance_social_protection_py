import React from "react";
import { AccountBalanceOutlined } from "@material-ui/icons";
import messages_en from "./translations/en.json";
import GrievanceMainMenu from "./menu/GrievanceMainMenu";
import reducer from "./reducer";
import GrievancePage from "./pages/GrievancePage";
import AddGrievance from "./pages/AddGrievance";
import { FormattedMessage } from "@openimis/fe-core";

import GrievanceStatusPicker from "./pickers/GrievanceStatusPicker";
import GrievanceTypePicker from "./pickers/GrievanceTypePicker";

const ROUTE_MY_GRIEVANCES = "grievances/my_grievances";
const ROUTE_ADD_GRIEVANCE = "grievances/add_grievance";

const DEFAULT_CONFIG = {
  "translations": [{ key: "en", messages: messages_en }],
  'reducers': [{ key:'grievance', reducer }],

  "refs": [
    
    { key: "grievance.route.my_grievance", ref: ROUTE_MY_GRIEVANCES },
    { key: "grievance.route.add_grievance", ref: ROUTE_ADD_GRIEVANCE },
    
    { key: "grievance.GrievanceStatusPicker", ref: GrievanceStatusPicker },
    { key: "grievance.GrievanceTypePicker", ref: GrievanceTypePicker },

  ],

  'core.MainMenu': [GrievanceMainMenu],
  "core.Router": [ 
    { path: ROUTE_MY_GRIEVANCES, component: GrievancePage },
    {path: ROUTE_ADD_GRIEVANCE, component: AddGrievance},
  ],
  "admin.MainMenu": [
    {
      text: <FormattedMessage module="grievance" id="menu.grievance" />,
      icon: <AccountBalanceOutlined />,
      route: "/" + ROUTE_MY_GRIEVANCES,
    },
  ],
}

export const GrievanceModule = (cfg) => {
  return { ...DEFAULT_CONFIG, ...cfg };
}