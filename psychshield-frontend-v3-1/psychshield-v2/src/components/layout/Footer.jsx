export default function Footer() {
  return (
    <footer className="border-t mt-24">
      <div className="mx-auto max-w-6xl px-6 py-8 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
        <p className="text-xs font-mono" style={{ color: "var(--color-text-tertiary)" }}>
          PsychShield — AI-Based Email Social Engineering Detection and Prediction System
        </p>
        <p className="text-xs" style={{ color: "var(--color-text-tertiary)" }}>
          Final-year research project · Caleb University, Dept. of Cybersecurity
        </p>
      </div>
    </footer>
  );
}
