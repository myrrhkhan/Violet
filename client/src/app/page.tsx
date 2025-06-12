"use client";
// import styles from "./page.module.css";
import dynamic from "next/dynamic";
const ExcalidrawWrapper = dynamic(
  () => import("./components/excalidrawWrapper"),
  { ssr: false },
);

// <div className={styles.page}>
// <main className={styles.main}>
// <footer className={styles.footer}></footer>

export default function Home() {
  return (
    <div>
      <main>
        <h1>Violet Handwriting to Text</h1>
        <ExcalidrawWrapper />
      </main>
      <footer></footer>
    </div>
  );
}
