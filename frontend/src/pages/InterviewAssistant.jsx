import { useState } from "react";
import ChatBox from "../components/ChatBox";
import StatusBar from "../components/StatusBar";
import Timeline from "../components/Timeline";
import ToolInspector from "../components/ToolInspector";

export default function InterviewAssistant() {
  const [activeAgent, setActiveAgent] = useState("Idle");
  const [timeline, setTimeline] = useState([]);
  const [toolLogs, setToolLogs] = useState([]);

  return (
    <div className="h-full flex flex-col bg-gradient-to-br from-indigo-200 via-sky-200 to-emerald-200">
      <StatusBar activeAgent={activeAgent} />

      <div className="flex flex-1 overflow-hidden">
        <div className="flex-1 p-4 overflow-hidden">
          <ChatBox
            onAgentChange={setActiveAgent}
            onTimelineUpdate={setTimeline}
            onToolLogsUpdate={setToolLogs}
          />
        </div>

        <div className="w-[380px] flex flex-col overflow-hidden rounded-l-3xl shadow-xl bg-gradient-to-br from-indigo-200/60 via-sky-200/60 to-emerald-200/60 backdrop-blur">
          <div className="flex-1 overflow-y-auto">
            <Timeline items={timeline} />
          </div>

          <div className="flex-1 overflow-y-auto">
            <ToolInspector items={toolLogs} />
          </div>
        </div>
      </div>
    </div>
  );
}
