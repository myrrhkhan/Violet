"use client";
import { Excalidraw, exportToBlob } from "@excalidraw/excalidraw";
import React, { useState } from "react";

import "@excalidraw/excalidraw/index.css";

const ExcalidrawWrapper: React.FC = () => {
  const [excalidrawAPI, setExcalidrawAPI] = useState(null);
  const [isClient, setIsClient] = useState(false);

  React.useEffect(() => {
    setIsClient(true);
  }, []);

  if (!isClient) {
    return <div style={{ height: "600px", width: "1100px" }}></div>;
  }

  return (
    <div>
      <button
        onClick={async () => {
          if (!excalidrawAPI) {
            return;
          }
          const elements = excalidrawAPI.getSceneElements();
          if (!elements || !elements.length) {
            return;
          }
          const appState = excalidrawAPI.getAppState();
          const files = excalidrawAPI.getFiles();
          // create blob
          const blob = await exportToBlob({
            elements,
            appState,
            files,
          });
          // submit to server
          console.log("sending");
          const response = await fetch(
            "https://fwkxoazxi2.execute-api.us-east-1.amazonaws.com/predict-ocr",
            {
              method: "POST",
              body: blob,
            },
          );
          const json = await response.text();
          const p = document.createElement("p");
          p.innerText = json;
          document.body.appendChild(p);
        }}
      >
        Export to Blob
      </button>
      <div style={{ height: "600px", width: "1100px" }}>
        <Excalidraw excalidrawAPI={(api) => setExcalidrawAPI(api)} />
      </div>
    </div>
  );
};
export default ExcalidrawWrapper;
