import React, { useState } from "react";
import { Tabs } from "@humansignal/ui";
import { SplitPage } from "../../features/pages/SplitPage";
import { EvaluationPage } from "../../features/pages/EvaluationPage";
import { useParams } from "react-router";

export const ModelTestingPage = () => {
  const { id: projectId } = useParams();
  const [activeTab, setActiveTab] = useState("splits");
  const [selectedSplit, setSelectedSplit] = useState(null);

  const handleStartEvaluation = (split) => {
    setSelectedSplit(split);
    setActiveTab("evaluations");
  };

  return (
    <div style={{ padding: "20px" }}>
      <Tabs value={activeTab} onChange={setActiveTab}>
        <Tabs.List>
          <Tabs.Trigger value="splits">数据集切割</Tabs.Trigger>
          <Tabs.Trigger value="evaluations">模型评估</Tabs.Trigger>
        </Tabs.List>
        <Tabs.Content value="splits">
          <SplitPage
            projectId={parseInt(projectId)}
            onStartEvaluation={handleStartEvaluation}
          />
        </Tabs.Content>
        <Tabs.Content value="evaluations">
          <EvaluationPage
            projectId={parseInt(projectId)}
            initialSplit={selectedSplit}
          />
        </Tabs.Content>
      </Tabs>
    </div>
  );
};

ModelTestingPage.title = "模型测试";
ModelTestingPage.path = "/model-testing";
