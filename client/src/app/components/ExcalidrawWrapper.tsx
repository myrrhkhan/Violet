"use client";
import { Excalidraw, exportToBlob } from "@excalidraw/excalidraw";
import React, { useState } from "react";

import "@excalidraw/excalidraw/index.css";

const ExcalidrawWrapper: React.FC = () => {
  const [excalidrawAPI, setExcalidrawAPI] = useState(null);
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
          const response = await fetch("http://192.168.1.205:8711/predict", {
            method: "POST",
            body: blob,
          });
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
