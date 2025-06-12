"use client";
import {
  Excalidraw,
  convertToExcalidrawElements,
} from "@excalidraw/excalidraw";

import "@excalidraw/excalidraw/index.css";

const ExcalidrawWrapper: React.FC = () => {
  return (
    <div style={{ height: "900px", width: "1600px" }}>
      <Excalidraw />
    </div>
  );
};
export default ExcalidrawWrapper;
