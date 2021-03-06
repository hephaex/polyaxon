import * as React from "react";
import * as _ from "lodash";

import Experiment from "./experiment";
import {ExperimentModel} from "../models/experiment";


export interface Props {
  experiments: ExperimentModel[];
  onCreate: (experiment: ExperimentModel) => any;
  onUpdate: (experiment: ExperimentModel) => any;
  onDelete: (experiment: ExperimentModel) => any;
  fetchData: () => any
}


export default class Experiments extends React.Component<Props, Object> {
  componentDidMount() {
    const {experiments, onCreate, onUpdate, onDelete, fetchData} = this.props;
    fetchData();
  }

  public render() {
    const {experiments, onCreate, onUpdate, onDelete, fetchData} = this.props;
    return (
      <div className="row">
        <div className="col-md-12">
          <ul>
            {experiments.filter(
              (xp: ExperimentModel) => _.isNil(xp.deleted) || !xp.deleted
            ).map(
              (xp: ExperimentModel) => <li className="list-item" key={xp.uuid}><Experiment
                experiment={xp} onDelete={() => onDelete(xp)}/></li>)}
          </ul>
        </div>
      </div>
    );
  }
}
