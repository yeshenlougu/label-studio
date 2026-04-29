import { makeAutoObservable, observable, action, computed } from 'mobx';

export interface SplitItem {
  id: number;
  name: string;
  split_type: string;
  config: Record<string, unknown>;
  status: string;
  total_tasks: number;
  train_tasks: number;
  test_tasks: number;
  created_at: string;
  created_by_email: string;
}

export interface EvaluationItem {
  id: number;
  name: string;
  split: number;
  split_name: string;
  model_versions: string[];
  status: string;
  summary_metrics: Record<string, number>;
  created_at: string;
  created_by_email: string;
  results: EvaluationResult[];
}

export interface EvaluationResult {
  model_version: string;
  metrics: Record<string, number>;
  per_class_metrics: Record<string, Record<string, number>>;
  confusion_matrix: {
    labels: string[];
    matrix: number[][];
  };
  error_samples: number[];
}

export interface Strategy {
  type: string;
  name: string;
  config_schema: {
    fields: ConfigField[];
  };
}

export interface ConfigField {
  name: string;
  type: string;
  label: string;
  default?: unknown;
  min?: number;
  max?: number;
  step?: number;
  options?: { value: string; label: string }[];
}

class ModelTestingStore {
  splits: SplitItem[] = [];
  evaluations: EvaluationItem[] = [];
  strategies: Strategy[] = [];
  currentSplit: SplitItem | null = null;
  currentEvaluation: EvaluationItem | null = null;
  loading = false;
  error: string | null = null;

  constructor() {
    makeAutoObservable(this);
  }

  @computed
  get splitOptions() {
    return this.splits.map((split) => ({
      value: split.id,
      label: split.name,
    }));
  }

  @action
  setSplits(splits: SplitItem[]) {
    this.splits = splits;
  }

  @action
  addSplit(split: SplitItem) {
    this.splits.push(split);
  }

  @action
  removeSplit(id: number) {
    this.splits = this.splits.filter((s) => s.id !== id);
  }

  @action
  setEvaluations(evaluations: EvaluationItem[]) {
    this.evaluations = evaluations;
  }

  @action
  addEvaluation(evaluation: EvaluationItem) {
    this.evaluations.push(evaluation);
  }

  @action
  setStrategies(strategies: Strategy[]) {
    this.strategies = strategies;
  }

  @action
  setCurrentSplit(split: SplitItem | null) {
    this.currentSplit = split;
  }

  @action
  setCurrentEvaluation(evaluation: EvaluationItem | null) {
    this.currentEvaluation = evaluation;
  }

  @action
  setLoading(loading: boolean) {
    this.loading = loading;
  }

  @action
  setError(error: string | null) {
    this.error = error;
  }

  @action
  clear() {
    this.splits = [];
    this.evaluations = [];
    this.currentSplit = null;
    this.currentEvaluation = null;
    this.error = null;
  }
}

export const modelTestingStore = new ModelTestingStore();
