import { readFileSync } from "node:fs";

const baseConfig = JSON.parse(
  readFileSync(new URL("./allurerc.json", import.meta.url), "utf-8"),
);

const numberStateValue = (value) => (Number.isFinite(value) ? Number(value) : 0);

const successRateStateValue = (value) => {
  if (typeof value !== "object" || value === null) {
    return { totalCount: 0, passedCount: 0 };
  }
  return {
    totalCount: numberStateValue(value.totalCount),
    passedCount: numberStateValue(value.passedCount),
  };
};

const isUnsuccessful = (tr) => tr.status === "failed" || tr.status === "broken";
const isSuccessful = (tr) => tr.status === "passed";
const isIncludedInSuccessRate = (tr) =>
  tr.status === "passed" || tr.status === "failed" || tr.status === "broken";

const formatQualityGateNumber = (value) => {
  if (!Number.isFinite(value)) {
    return String(value);
  }
  return Number.isInteger(value) ? String(value) : String(Number(value.toFixed(2)));
};

const formatMetricValue = (value, unit) => {
  if (typeof value === "string") {
    return value;
  }
  if (!Number.isFinite(value)) {
    return "n/a";
  }
  const formatted = formatQualityGateNumber(value);
  if (!unit) {
    return formatted;
  }
  return unit === "%" ? `${formatted}%` : `${formatted} ${unit}`;
};

const metricValues = (metrics, key) =>
  metrics
    .map((metric) => (metric.key === key ? metric.value : undefined))
    .filter((value) => Number.isFinite(value));

const metricAverage = (metrics, key) => {
  const values = metricValues(metrics, key);
  if (values.length === 0) {
    return undefined;
  }
  return values.reduce((acc, value) => acc + value, 0) / values.length;
};

const metricRuleTitle = (metrics, expected) => {
  const sample = metrics.find((metric) => metric.key === expected?.key);
  return sample?.title ?? expected?.title ?? expected?.key ?? "Metric";
};

const metricRuleUnit = (metrics, expected) => {
  const sample = metrics.find((metric) => metric.key === expected?.key);
  return sample?.unit ?? expected?.unit;
};

const maxFailuresRule = {
  rule: "maxFailures",
  message: ({ actual, expected }) =>
    `The number of failed tests ${actual} exceeds the allowed threshold value ${expected}`,
  successMessage: ({ actual, expected }) =>
    `The number of failed tests ${actual} is within the allowed threshold value ${expected}`,
  validate: async ({ trs, expected, state }) => {
    const previous = numberStateValue(state.getResult());
    const failedTrs = trs.filter(isUnsuccessful);
    const testResults = failedTrs.map((tr) => tr.id);
    const actual = previous + failedTrs.length;
    state.setResult(actual, testResults);
    return {
      success: actual <= expected,
      actual,
      testResults,
    };
  },
};

const minTestsCountRule = {
  rule: "minTestsCount",
  message: ({ actual, expected }) =>
    `The total number of tests ${actual} is less than the expected threshold value ${expected}`,
  successMessage: ({ actual, expected }) =>
    `The total number of tests ${actual} meets the expected threshold value ${expected}`,
  validate: async ({ trs, expected, state }) => {
    const actual = trs.length + numberStateValue(state.getResult());
    state.setResult(actual, []);
    return {
      success: actual >= expected,
      actual,
      testResults: [],
    };
  },
};

const successRateRule = {
  rule: "successRate",
  message: ({ actual, expected }) =>
    `Success rate ${formatQualityGateNumber(actual)} is less, than expected ${formatQualityGateNumber(expected)}`,
  successMessage: ({ actual, expected }) =>
    `Success rate ${formatQualityGateNumber(actual)} is not less, than expected ${formatQualityGateNumber(expected)}`,
  validate: async ({ trs, expected, state }) => {
    const previous = successRateStateValue(state.getResult());
    const eligibleTrs = trs.filter(isIncludedInSuccessRate);
    const passedTrs = eligibleTrs.filter(isSuccessful);
    const notPassedTrs = eligibleTrs.filter(isUnsuccessful);
    const totalCount = previous.totalCount + eligibleTrs.length;
    const passedCount = previous.passedCount + passedTrs.length;
    const testResults = notPassedTrs.map((tr) => tr.id);
    const rate = totalCount === 0 ? 0 : passedCount / totalCount;
    state.setResult({ totalCount, passedCount }, testResults);
    return {
      success: rate >= expected,
      actual: rate,
      testResults,
    };
  },
};

const maxDurationRule = {
  rule: "maxDuration",
  message: ({ actual, expected }) =>
    `Maximum duration of some tests exceed the defined limit; actual ${actual}, expected ${expected}`,
  successMessage: ({ actual, expected }) =>
    `Maximum duration of the tests is within the defined limit; actual ${actual}, expected ${expected}`,
  validate: async ({ trs, expected, state }) => {
    const previous = numberStateValue(state.getResult());
    const actual = Math.max(previous, ...trs.map((tr) => tr.duration ?? 0));
    const tooLongTrs = trs.filter((tr) => (tr.duration ?? 0) > expected);
    const testResults = tooLongTrs.map((tr) => tr.id);
    state.setResult(actual, testResults);
    return {
      success: actual <= expected,
      actual,
      testResults,
    };
  },
};

const metricMinRule = {
  rule: "metricMin",
  message: ({ actual, expected }) => {
    const title = expected?.title ?? expected?.key ?? "Metric";
    const expectedFormatted = formatMetricValue(expected?.value, expected?.unit);
    return `${title} is below the required minimum; actual ${actual}, expected >= ${expectedFormatted}`;
  },
  successMessage: ({ actual, expected }) => {
    const title = expected?.title ?? expected?.key ?? "Metric";
    const expectedFormatted = formatMetricValue(expected?.value, expected?.unit);
    return `${title} is within the defined limit; actual ${actual}, expected >= ${expectedFormatted}`;
  },
  validate: async ({ metrics = [], expected }) => {
    const value = metricAverage(metrics, expected.key);
    const unit = metricRuleUnit(metrics, expected);
    const title = metricRuleTitle(metrics, expected);
    return {
      success: value !== undefined && value >= expected.value,
      actual: formatMetricValue(value ?? Number.NaN, unit),
      title,
      testResults: [],
    };
  },
};

const metricMaxRule = {
  rule: "metricMax",
  message: ({ actual, expected }) => {
    const title = expected?.title ?? expected?.key ?? "Metric";
    const expectedFormatted = formatMetricValue(expected?.value, expected?.unit);
    return `${title} exceeds the allowed maximum; actual ${actual}, expected <= ${expectedFormatted}`;
  },
  successMessage: ({ actual, expected }) => {
    const title = expected?.title ?? expected?.key ?? "Metric";
    const expectedFormatted = formatMetricValue(expected?.value, expected?.unit);
    return `${title} is within the defined limit; actual ${actual}, expected <= ${expectedFormatted}`;
  },
  validate: async ({ metrics = [], expected }) => {
    const value = metricAverage(metrics, expected.key);
    const unit = metricRuleUnit(metrics, expected);
    const title = metricRuleTitle(metrics, expected);
    return {
      success: value !== undefined && value <= expected.value,
      actual: formatMetricValue(value ?? Number.NaN, unit),
      title,
      testResults: [],
    };
  },
};

export default {
  ...baseConfig,
  qualityGate: {
    ...baseConfig.qualityGate,
    use: [
      maxFailuresRule,
      minTestsCountRule,
      successRateRule,
      maxDurationRule,
      metricMinRule,
      metricMaxRule,
    ],
  },
};
