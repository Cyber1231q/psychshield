import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ScanLine, Loader2, Link2, ShieldAlert, Brain, FileText, Upload, Mail, AlertTriangle, ChevronDown, ChevronUp } from "lucide-react";
import TriggerMap from "../components/triggers/TriggerMap";
import RiskBadge from "../components/ui/RiskBadge";
import SenderVerification from "../components/ui/SenderVerification";
import PreClickWarning from "../components/ui/PreClickWarning";
import GmailConnect from "../components/gmail/GmailConnect";
import GmailScanPanel from "../components/gmail/GmailScanPanel";
import { api } from "../lib/api";
import ScrollReveal from "../components/ui/ScrollReveal";

// Upload safety limits — bound memory/CPU use for a client-side-only
// parsing pipeline (no backend file endpoint exists; everything here
// runs in the browser tab) and mirror the backend's own field limits
// (EmailAnalysisRequest in models/schemas.py) so requests don't fail
// with an opaque validation error after all the parsing work is done.
const MAX_UPLOAD_BYTES = 10 * 1024 * 1024; // 10 MB raw file
const MAX_EXTRACTED_CHARS = 100000; // extracted text kept in the UI
const MAX_BODY_CHARS = 50000; // matches EmailAnalysisRequest.body
const MAX_SENDER_CHARS = 254; // matches EmailAnalysisRequest.sender
const MAX_DOCX_XML_CHARS = 5_000_000; // guards against a zip-bomb document.xml
const MAX_PDF_PAGES = 300;
const MAX_PDF_CHARS = 2_000_000;

function truncateText(text, max = MAX_EXTRACTED_CHARS) {
  return text.length > max ? text.slice(0, max) : text;
}

async function readFileSignature(file, numBytes = 8) {
  const buf = await file.slice(0, numBytes).arrayBuffer();
  return new Uint8Array(buf);
}

function isZipSignature(bytes) {
  // .docx (and any OOXML) file is a ZIP archive: "PK" magic bytes.
  return bytes.length >= 2 && bytes[0] === 0x50 && bytes[1] === 0x4b;
}

function isPdfSignature(bytes) {
  // "%PDF" magic bytes.
  return bytes.length >= 4 && bytes[0] === 0x25 && bytes[1] === 0x50 && bytes[2] === 0x44 && bytes[3] === 0x46;
}

function parseEmailHeaders(raw) {
  const headers = {};
  const lines = raw.replace(/\r\n/g, "\n").split("\n");
  let i = 0;
  let lastKey = "";
  for (; i < lines.length; i++) {
    const line = lines[i];
    if (line === "") break;
    if (/^\s/.test(line) && lastKey) {
      headers[lastKey] += " " + line.trim();
    } else {
      const sep = line.indexOf(":");
      if (sep > 0) {
        const key = line.slice(0, sep).trim().toLowerCase();
        const val = line.slice(sep + 1).trim();
        headers[key] = val;
        lastKey = key;
      }
    }
  }
  const body = lines.slice(i + 1).join("\n").trim();
  let sender = "";
  const fromField = headers["from"] || "";
  const emailMatch = fromField.match(/[\w.+-]+@[\w.-]+\.\w{2,}/);
  if (emailMatch) sender = emailMatch[0];
  return { headers, body, sender };
}

function extractSender(text) {
  const fromLine = text.match(/^From:\s*(.+)/im);
  if (fromLine) {
    const em = fromLine[1].match(/[\w.+-]+@[\w.-]+\.\w{2,}/);
    if (em) return em[0];
    return fromLine[1].trim();
  }
  return "";
}

function extractSubject(text) {
  const subLine = text.match(/^Subject:\s*(.+)/im);
  if (subLine) return subLine[1].trim().slice(0, 100);
  const first = text.trim().split("\n")[0]?.trim() || "";
  return first.slice(0, 80);
}

function splitEmails(text) {
  const separators = /\n-{3,}\n|\n={3,}\n|\n\*{3,}\n/;
  let chunks = text.split(separators).map((c) => c.trim()).filter((c) => c.length > 10);
  if (chunks.length > 1) return chunks;

  chunks = [];
  let current = "";
  for (const line of text.split("\n")) {
    if (/^From:\s*.+@/i.test(line) && current.trim().length > 30) {
      chunks.push(current.trim());
      current = line + "\n";
    } else {
      current += line + "\n";
    }
  }
  if (current.trim().length > 10) chunks.push(current.trim());
  if (chunks.length > 1) return chunks;

  chunks = [];
  current = "";
  for (const line of text.split("\n")) {
    if (/^(email\s*#?\s*\d+|sample\s*#?\s*\d+|\d+[\.\)]\s)/i.test(line) && current.trim().length > 20) {
      chunks.push(current.trim());
      current = line + "\n";
    } else {
      current += line + "\n";
    }
  }
  if (current.trim().length > 10) chunks.push(current.trim());
  if (chunks.length > 1) return chunks;

  return [text.trim()];
}

function SingleResult({ result, emailText }) {
  return (
    <div className="space-y-5">
      <ScrollReveal>
        <PreClickWarning tier={result.riskTier} score={result.riskScore} />
      </ScrollReveal>

      {result.riskTier === "High" && (
        <ScrollReveal delay={0.1}>
        <div className="rounded-2xl border-2 p-6" style={{ backgroundColor: "var(--color-risk-high-soft)", borderColor: "var(--color-risk-high)" }}>
          <div className="flex items-center gap-2 mb-4">
            <AlertTriangle size={18} style={{ color: "var(--color-risk-high)" }} />
            <span className="text-sm font-bold uppercase tracking-wide" style={{ color: "var(--color-risk-high)" }}>
              High Risk Email — Full Content Preserved for Investigation
            </span>
          </div>
          <div className="rounded-xl p-4 mb-4" style={{ backgroundColor: "var(--color-bg-sunken)" }}>
            <p className="text-[11px] font-mono uppercase tracking-wide mb-2" style={{ color: "var(--color-text-tertiary)" }}>Sender identification</p>
            <div className="space-y-2">
              <div className="flex items-start gap-2">
                <span className="text-xs font-mono shrink-0 w-20" style={{ color: "var(--color-text-tertiary)" }}>From:</span>
                <span className="text-sm font-mono font-semibold break-all" style={{ color: "var(--color-risk-high)" }}>
                  {result.sender || result.senderVerification?.from || "Unknown sender"}
                </span>
              </div>
              {result.senderVerification && (
                <>
                  <div className="flex items-start gap-2">
                    <span className="text-xs font-mono shrink-0 w-20" style={{ color: "var(--color-text-tertiary)" }}>Domain:</span>
                    <span className="text-sm font-mono break-all" style={{ color: "var(--color-text-primary)" }}>
                      {result.senderVerification.domain || "Unknown"}
                    </span>
                    {result.senderVerification.typosquatted && (
                      <span className="shrink-0 rounded px-1.5 py-0.5 text-[10px] font-mono font-semibold" style={{ backgroundColor: "var(--color-risk-high-soft)", color: "var(--color-risk-high)" }}>TYPOSQUATTED</span>
                    )}
                  </div>
                  <div className="flex items-center gap-4 mt-2 pt-2 border-t">
                    <span className="text-xs font-mono" style={{ color: result.senderVerification.spf === "FAIL" ? "var(--color-risk-high)" : "var(--color-text-tertiary)" }}>SPF: {result.senderVerification.spf}</span>
                    <span className="text-xs font-mono" style={{ color: result.senderVerification.dkim === "FAIL" ? "var(--color-risk-high)" : "var(--color-text-tertiary)" }}>DKIM: {result.senderVerification.dkim}</span>
                    <span className="text-xs font-mono" style={{ color: result.senderVerification.dmarc === "FAIL" ? "var(--color-risk-high)" : "var(--color-text-tertiary)" }}>DMARC: {result.senderVerification.dmarc}</span>
                  </div>
                </>
              )}
            </div>
          </div>
          <div className="rounded-xl p-4" style={{ backgroundColor: "var(--color-bg-sunken)" }}>
            <p className="text-[11px] font-mono uppercase tracking-wide mb-2" style={{ color: "var(--color-text-tertiary)" }}>Full email content (preserved for investigation)</p>
            <pre className="text-xs font-mono leading-relaxed whitespace-pre-wrap break-words max-h-[300px] overflow-y-auto" style={{ color: "var(--color-text-primary)" }}>
              {result.bodyPreview || emailText}
            </pre>
          </div>
          {result.linkVerification?.urls?.length > 0 && (
            <div className="rounded-xl p-4 mt-4" style={{ backgroundColor: "var(--color-bg-sunken)" }}>
              <p className="text-[11px] font-mono uppercase tracking-wide mb-2" style={{ color: "var(--color-text-tertiary)" }}>Dangerous links found</p>
              {result.linkVerification.urls.map((u) => (
                <div key={u.url} className="mb-2 last:mb-0">
                  <p className="text-xs font-mono break-all" style={{ color: "var(--color-risk-high)" }}>{u.url}</p>
                  <div className="mt-1 space-y-0.5">{u.flags.map((f) => <p key={f} className="text-[11px] pl-3" style={{ color: "var(--color-text-secondary)" }}>· {f}</p>)}</div>
                </div>
              ))}
            </div>
          )}
          <p className="mt-4 text-xs" style={{ color: "var(--color-risk-high)" }}>This content has been preserved for security investigation. Do not click any links or reply to this sender.</p>
        </div>
        </ScrollReveal>
      )}

      <ScrollReveal delay={0.15}>
      <div className="rounded-2xl border p-5" style={{ backgroundColor: "var(--color-bg-elevated)" }}>
        <div className="flex items-center justify-between">
          <span className="text-xs font-mono uppercase tracking-wide" style={{ color: "var(--color-text-tertiary)" }}>Composite risk score</span>
          <RiskBadge tier={result.riskTier} score={result.riskScore} />
        </div>
        <p className="mt-3 text-sm leading-relaxed" style={{ color: "var(--color-text-secondary)" }}>{result.riskReport.explanation}</p>
        <p className="mt-3 text-[11px] font-mono" style={{ color: "var(--color-text-tertiary)" }}>{result.riskReport.weightedFormula}</p>
      </div>
      </ScrollReveal>

      <ScrollReveal delay={0.2}>
      <div className="rounded-2xl border p-5" style={{ backgroundColor: "var(--color-bg-elevated)" }}>
        <div className="flex items-center gap-2 mb-4">
          <Brain size={15} style={{ color: "var(--color-accent)" }} />
          <span className="text-xs font-mono uppercase tracking-wide" style={{ color: "var(--color-text-tertiary)" }}>Psychological trigger map</span>
        </div>
        <TriggerMap triggers={result.triggers} />
      </div>
      </ScrollReveal>

      <ScrollReveal delay={0.25}>
      <div className="rounded-2xl border p-5" style={{ backgroundColor: "var(--color-bg-elevated)" }}>
        <div className="flex items-center gap-2 mb-4">
          <ShieldAlert size={15} style={{ color: "var(--color-accent)" }} />
          <span className="text-xs font-mono uppercase tracking-wide" style={{ color: "var(--color-text-tertiary)" }}>Manipulation techniques detected</span>
        </div>
        <ul className="space-y-2.5">
          {result.manipulationPattern.techniques.map((t) => (
            <li key={t.name} className="flex items-start gap-2.5 text-sm">
              <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full" style={{ backgroundColor: "var(--color-accent)" }} />
              <span style={{ color: "var(--color-text-primary)" }}>
                <span className="font-medium">{t.name}</span>
                <span className="block text-xs mt-0.5 font-mono" style={{ color: "var(--color-text-tertiary)" }}>{t.evidence}</span>
              </span>
            </li>
          ))}
        </ul>
      </div>
      </ScrollReveal>

      <ScrollReveal delay={0.3}>
      <div className="rounded-2xl border p-5" style={{ backgroundColor: "var(--color-bg-elevated)" }}>
        <div className="flex items-center gap-2 mb-4">
          <Link2 size={15} style={{ color: "var(--color-accent)" }} />
          <span className="text-xs font-mono uppercase tracking-wide" style={{ color: "var(--color-text-tertiary)" }}>Link verification</span>
        </div>
        {result.linkVerification.urls.length > 0
          ? result.linkVerification.urls.map((u) => (
              <div key={u.url} className="rounded-lg p-3" style={{ backgroundColor: "var(--color-risk-high-soft)" }}>
                <p className="font-mono text-xs break-all" style={{ color: "var(--color-risk-high)" }}>{u.url}</p>
                <ul className="mt-2 space-y-1">{u.flags.map((f) => <li key={f} className="text-xs" style={{ color: "var(--color-text-secondary)" }}>· {f}</li>)}</ul>
              </div>
            ))
          : <p className="text-xs" style={{ color: "var(--color-text-tertiary)" }}>No URLs found in this email.</p>}
      </div>
      </ScrollReveal>

      <ScrollReveal delay={0.35}>
        <SenderVerification sender={result.senderVerification} />
      </ScrollReveal>
    </div>
  );
}

export default function EmailAnalysis() {
  const [activeTab, setActiveTab] = useState("paste"); // "paste" | "gmail"
  const [gmailConnected, setGmailConnected] = useState(false);
  const [gmailNotice, setGmailNotice] = useState(null); // "connected" | "error" | null

  // Handle redirect back from Google OAuth: /analysis?gmail=connected
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const status = params.get("gmail");
    if (status === "connected") {
      setActiveTab("gmail");
      setGmailConnected(true);
      setGmailNotice("connected");
      window.history.replaceState({}, "", window.location.pathname);
    } else if (status === "error") {
      setActiveTab("gmail");
      setGmailNotice("error");
      window.history.replaceState({}, "", window.location.pathname);
    }
  }, []);

  const [emailText, setEmailText] = useState("");
  const [senderEmail, setSenderEmail] = useState("");
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [result, setResult] = useState(null);
  const [parsedHeaders, setParsedHeaders] = useState(null);
  const [uploadError, setUploadError] = useState("");

  const [batchEmails, setBatchEmails] = useState([]);
  const [batchResults, setBatchResults] = useState([]);
  const [batchProgress, setBatchProgress] = useState(0);
  const [expandedBatch, setExpandedBatch] = useState(null);

  const isBatchMode = batchEmails.length > 1;

  async function handleAnalyze() {
    setIsAnalyzing(true);
    setResult(null);
    setBatchResults([]);
    setBatchProgress(0);

    if (isBatchMode) {
      const results = [];
      for (let i = 0; i < batchEmails.length; i++) {
        setBatchProgress(i + 1);
        try {
          const data = await api.analyzeEmail({
            body: batchEmails[i].body.slice(0, MAX_BODY_CHARS),
            sender: batchEmails[i].sender ? batchEmails[i].sender.slice(0, MAX_SENDER_CHARS) : undefined,
          });
          results.push({ ...data, _index: i, _originalBody: batchEmails[i].body });
        } catch (err) {
          results.push({ _index: i, _error: true, _originalBody: batchEmails[i].body, riskScore: 0, riskTier: "Error" });
        }
      }
      setBatchResults(results);
    } else {
      try {
        const data = await api.analyzeEmail({
          body: emailText.slice(0, MAX_BODY_CHARS),
          sender: senderEmail ? senderEmail.slice(0, MAX_SENDER_CHARS) : undefined,
        });
        setResult(data);
      } catch (err) {
        console.error("Analysis failed:", err);
      }
    }
    setIsAnalyzing(false);
  }

  async function extractDocxText(file) {
    const JSZip = (await import("jszip")).default;
    const buf = await file.arrayBuffer();
    const zip = await JSZip.loadAsync(buf);
    const entry = zip.file("word/document.xml");
    if (!entry) throw new Error("No document.xml found");
    const docXml = await entry.async("string");
    if (docXml.length > MAX_DOCX_XML_CHARS) throw new Error("TOO_LARGE");
    return docXml.replace(/<[^>]+>/g, " ").replace(/\s+/g, " ").trim();
  }

  async function extractPdfText(file) {
    const pdfjsLib = await import("pdfjs-dist");
    const { default: workerSrc } = await import("pdfjs-dist/build/pdf.worker.mjs?url");
    pdfjsLib.GlobalWorkerOptions.workerSrc = workerSrc;

    const buf = await file.arrayBuffer();
    const pdf = await pdfjsLib.getDocument({ data: buf }).promise;
    const pageCount = Math.min(pdf.numPages, MAX_PDF_PAGES);

    let text = "";
    for (let i = 1; i <= pageCount; i++) {
      const page = await pdf.getPage(i);
      const content = await page.getTextContent();
      text += content.items.map((item) => item.str).join(" ") + "\n";
      if (text.length > MAX_PDF_CHARS) {
        text = text.slice(0, MAX_PDF_CHARS);
        break;
      }
    }
    return text.trim();
  }

  function processFileText(raw) {
    const hasHeaders = /^(from|to|subject|date|received|mime-version|content-type):/im.test(raw);
    if (hasHeaders) {
      const parsed = parseEmailHeaders(raw);
      setParsedHeaders(parsed.headers);
      if (parsed.sender) setSenderEmail(parsed.sender);
      raw = parsed.body;
    } else {
      setParsedHeaders(null);
    }

    const chunks = splitEmails(raw);
    if (chunks.length > 1) {
      const emails = chunks.map((chunk) => ({
        body: chunk,
        sender: extractSender(chunk),
        subject: extractSubject(chunk),
      }));
      setBatchEmails(emails);
      setEmailText(raw);
      setResult(null);
      setBatchResults([]);
    } else {
      setBatchEmails([]);
      setEmailText(raw);
      if (!senderEmail) {
        const s = extractSender(raw);
        if (s) setSenderEmail(s);
      }
    }
  }

  async function handleFileUpload(e) {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploadError("");
    setBatchEmails([]);
    setBatchResults([]);
    setResult(null);

    if (file.size > MAX_UPLOAD_BYTES) {
      setUploadError(`File is too large (${(file.size / (1024 * 1024)).toFixed(1)} MB). Max allowed size is ${MAX_UPLOAD_BYTES / (1024 * 1024)} MB.`);
      e.target.value = "";
      return;
    }

    const name = file.name.toLowerCase();
    const signature = await readFileSignature(file);
    const finish = (text) => {
      processFileText(truncateText(text));
      if (text.length > MAX_EXTRACTED_CHARS) {
        setUploadError(`Note: extracted text was truncated to ${MAX_EXTRACTED_CHARS.toLocaleString()} characters.`);
      }
    };

    if (name.endsWith(".docx")) {
      if (!isZipSignature(signature)) {
        setUploadError("This .docx file is corrupted or its content doesn't match a real Word document.");
        e.target.value = "";
        return;
      }
      try {
        const text = await extractDocxText(file);
        if (!text) { setUploadError("Could not extract text from this .docx file."); return; }
        finish(text);
      } catch (err) {
        setUploadError(err.message === "TOO_LARGE" ? "This document is too large or complex to process." : "Failed to read .docx file. Try saving as .txt instead.");
      }
      e.target.value = "";
      return;
    }

    if (name.endsWith(".pdf")) {
      if (!isPdfSignature(signature)) {
        setUploadError("This .pdf file is corrupted or its content doesn't match a real PDF.");
        e.target.value = "";
        return;
      }
      try {
        const text = await extractPdfText(file);
        if (!text) { setUploadError("Could not extract text from this PDF (it may be scanned/image-only)."); return; }
        finish(text);
      } catch {
        setUploadError("Failed to read PDF file. Try saving as .txt instead.");
      }
      e.target.value = "";
      return;
    }

    const allowed = [".eml", ".txt", ".msg", ".mbox"];
    if (!allowed.some((ext) => name.endsWith(ext))) {
      setUploadError(`Unsupported file type. Upload .eml, .txt, .msg, .mbox, .docx, or .pdf files. Received: .${name.split(".").pop()}`);
      e.target.value = "";
      return;
    }

    if (isZipSignature(signature) || isPdfSignature(signature)) {
      setUploadError("This file's content doesn't match its extension. Rename it with the correct extension (.docx or .pdf) and re-upload.");
      e.target.value = "";
      return;
    }

    const reader = new FileReader();
    reader.onload = (ev) => {
      const raw = ev.target.result;
      // Intentional: detecting binary content disguised as text, not matching literal text.
      // eslint-disable-next-line no-control-regex
      if (/[\x00-\x08\x0E-\x1F]/.test(raw.slice(0, 500))) {
        setUploadError("This file contains binary data. Please paste the email text directly or save as .txt first.");
        return;
      }
      finish(raw);
    };
    reader.onerror = () => setUploadError("Failed to read file.");
    reader.readAsText(file);
  }

  const highCount = batchResults.filter((r) => r.riskTier === "High").length;
  const medCount = batchResults.filter((r) => r.riskTier === "Medium").length;
  const lowCount = batchResults.filter((r) => r.riskTier === "Low").length;

  return (
    <div className="mx-auto max-w-6xl px-6 py-12">
      <div className="mb-6">
        <p className="text-xs font-mono uppercase tracking-wide" style={{ color: "var(--color-accent)" }}>Analysis interface</p>
        <h1 className="mt-2 text-3xl font-bold tracking-tight" style={{ color: "var(--color-text-primary)" }}>
          Decompose an email before you act on it
        </h1>
        <p className="mt-2 max-w-2xl text-sm" style={{ color: "var(--color-text-secondary)" }}>
          Paste email content, upload a file, or connect Gmail to scan your inbox directly.
        </p>
      </div>

      {/* Tab bar */}
      <div className="flex gap-1 mb-6 p-1 rounded-xl w-fit" style={{ backgroundColor: "var(--color-bg-elevated)" }}>
        {[
          { id: "paste", label: "Paste / Upload", icon: FileText },
          { id: "gmail", label: "Gmail Inbox", icon: Mail },
        ].map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            onClick={() => setActiveTab(id)}
            className="flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium transition-all"
            style={{
              backgroundColor: activeTab === id ? "var(--color-accent)" : "transparent",
              color: activeTab === id ? "#fff" : "var(--color-text-secondary)",
            }}
          >
            <Icon size={14} />
            {label}
          </button>
        ))}
      </div>

      {/* Gmail OAuth callback notices */}
      <AnimatePresence>
        {gmailNotice === "connected" && (
          <motion.div
            initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
            className="mb-5 flex items-center gap-2 rounded-xl px-4 py-3 text-sm font-medium"
            style={{ backgroundColor: "var(--color-risk-low-soft)", color: "var(--color-risk-low)" }}
          >
            Gmail connected successfully. You can now scan your inbox below.
            <button onClick={() => setGmailNotice(null)} className="ml-auto text-xs opacity-60 hover:opacity-100">✕</button>
          </motion.div>
        )}
        {gmailNotice === "error" && (
          <motion.div
            initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
            className="mb-5 flex items-center gap-2 rounded-xl px-4 py-3 text-sm"
            style={{ backgroundColor: "var(--color-risk-high-soft)", color: "var(--color-risk-high)" }}
          >
            <AlertTriangle size={14} />
            Gmail authorization failed. Please try connecting again.
            <button onClick={() => setGmailNotice(null)} className="ml-auto text-xs opacity-60 hover:opacity-100">✕</button>
          </motion.div>
        )}
      </AnimatePresence>

      {/* ── PASTE / UPLOAD TAB ─────────────────────────────────── */}
      {activeTab === "paste" && (
      <div className="grid gap-6 lg:grid-cols-[1fr_1fr] lg:items-start">
        {/* INPUT PANEL */}
        <div className="rounded-2xl border p-5" style={{ backgroundColor: "var(--color-bg-elevated)" }}>
          <div className="flex items-center justify-between gap-2 mb-3">
            <div className="flex items-center gap-2">
              <FileText size={15} style={{ color: "var(--color-text-tertiary)" }} />
              <span className="text-xs font-mono" style={{ color: "var(--color-text-tertiary)" }}>.txt / .eml / .docx / .pdf</span>
            </div>
            <label className="focus-ring inline-flex cursor-pointer items-center gap-1.5 rounded-md border px-3 py-1.5 text-xs font-medium transition-colors hover:opacity-80" style={{ borderColor: "var(--color-border-strong)", color: "var(--color-text-secondary)" }}>
              <Upload size={12} />
              Upload file
              <input type="file" accept=".eml,.txt,.msg,.mbox,.docx,.pdf,message/rfc822,application/pdf" className="sr-only" onChange={handleFileUpload} />
            </label>
          </div>

          {uploadError && (
            <div className="mb-3 flex items-start gap-2.5 rounded-lg p-3 text-xs" style={{ backgroundColor: "var(--color-risk-high-soft)", color: "var(--color-risk-high)" }}>
              <AlertTriangle size={14} className="mt-0.5 shrink-0" />
              <span>{uploadError}</span>
            </div>
          )}

          {isBatchMode && (
            <div className="mb-3 rounded-lg border p-3" style={{ backgroundColor: "var(--color-accent-soft)", borderColor: "var(--color-accent)" }}>
              <p className="text-xs font-semibold" style={{ color: "var(--color-accent)" }}>
                {batchEmails.length} emails detected in file — each will be analyzed separately
              </p>
              <div className="mt-2 space-y-1 max-h-[150px] overflow-y-auto">
                {batchEmails.map((em, i) => (
                  <div key={i} className="flex items-center gap-2 text-[11px] font-mono" style={{ color: "var(--color-text-secondary)" }}>
                    <span style={{ color: "var(--color-accent)" }}>#{i + 1}</span>
                    <span className="truncate">{em.sender || "No sender"}</span>
                    <span className="text-[10px] truncate flex-1" style={{ color: "var(--color-text-tertiary)" }}>{em.subject}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {!isBatchMode && (
            <div className="mb-3">
              <div className="flex items-center gap-2 mb-1.5">
                <Mail size={14} style={{ color: "var(--color-text-tertiary)" }} />
                <label className="text-xs font-mono" style={{ color: "var(--color-text-tertiary)" }}>Sender email address</label>
              </div>
              <input
                type="email" value={senderEmail} onChange={(e) => setSenderEmail(e.target.value)}
                className="focus-ring w-full rounded-lg border px-4 py-2.5 text-[13px] font-mono"
                style={{ backgroundColor: "var(--color-bg-sunken)", color: "var(--color-text-primary)", borderColor: "var(--color-border)" }}
                placeholder="e.g. security@paypa1-support.com"
              />
            </div>
          )}

          {parsedHeaders && !isBatchMode && (
            <div className="mb-3 rounded-lg border p-3 space-y-1.5" style={{ backgroundColor: "var(--color-bg-sunken)", borderColor: "var(--color-border)" }}>
              <p className="text-[10px] font-mono uppercase tracking-wide mb-2" style={{ color: "var(--color-accent)" }}>Parsed email headers</p>
              {[["From", parsedHeaders["from"]], ["To", parsedHeaders["to"]], ["Subject", parsedHeaders["subject"]], ["Date", parsedHeaders["date"]], ["Reply-To", parsedHeaders["reply-to"]]]
                .filter(([, v]) => v)
                .map(([label, value]) => (
                  <div key={label} className="flex items-start gap-2">
                    <span className="text-[11px] font-mono shrink-0 w-20" style={{ color: "var(--color-text-tertiary)" }}>{label}:</span>
                    <span className="text-[11px] font-mono break-all" style={{ color: label === "From" ? "var(--color-text-primary)" : "var(--color-text-secondary)", fontWeight: label === "From" ? 600 : 400 }}>{value}</span>
                  </div>
                ))}
              <button type="button" onClick={() => setParsedHeaders(null)} className="mt-1 text-[10px] font-mono" style={{ color: "var(--color-text-tertiary)" }}>Dismiss</button>
            </div>
          )}

          <textarea
            value={emailText} onChange={(e) => { setEmailText(e.target.value); setBatchEmails([]); setBatchResults([]); }}
            rows={isBatchMode ? 6 : 14}
            className="focus-ring w-full resize-none rounded-lg border p-4 text-[13px] leading-relaxed font-mono"
            style={{ backgroundColor: "var(--color-bg-sunken)", color: "var(--color-text-primary)", borderColor: "var(--color-border)" }}
            placeholder="Paste email content here..."
          />

          <button
            type="button" onClick={handleAnalyze} disabled={isAnalyzing || (!emailText.trim() && !isBatchMode)}
            className="focus-ring mt-4 inline-flex w-full items-center justify-center gap-2 rounded-lg px-5 py-3 text-sm font-semibold transition-opacity disabled:opacity-50"
            style={{ backgroundColor: "var(--color-accent)", color: "var(--color-bg-elevated)" }}
          >
            {isAnalyzing ? (
              <><Loader2 size={16} className="animate-spin" />{isBatchMode ? `Analyzing ${batchProgress}/${batchEmails.length}...` : "Running pipeline..."}</>
            ) : (
              <><ScanLine size={16} />{isBatchMode ? `Analyze all ${batchEmails.length} emails` : "Analyze email"}</>
            )}
          </button>
        </div>

        {/* RESULTS PANEL */}
        <div className="min-h-[420px]">
          <AnimatePresence mode="wait">
            {!result && batchResults.length === 0 && !isAnalyzing && (
              <motion.div key="empty" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                className="flex h-full min-h-[420px] flex-col items-center justify-center rounded-2xl border border-dashed p-8 text-center">
                <ShieldAlert size={28} style={{ color: "var(--color-text-tertiary)" }} />
                <p className="mt-3 text-sm" style={{ color: "var(--color-text-tertiary)" }}>Results will appear here once analysis runs.</p>
              </motion.div>
            )}

            {isAnalyzing && (
              <motion.div key="loading" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                className="flex h-full min-h-[420px] flex-col items-center justify-center rounded-2xl border p-8 text-center"
                style={{ backgroundColor: "var(--color-bg-elevated)" }}>
                <Loader2 size={24} className="animate-spin" style={{ color: "var(--color-accent)" }} />
                <p className="mt-3 text-sm" style={{ color: "var(--color-text-secondary)" }}>
                  {isBatchMode ? `Analyzing email ${batchProgress} of ${batchEmails.length}...` : "Running emotion, manipulation, and link analysis in parallel..."}
                </p>
                {isBatchMode && (
                  <div className="w-full max-w-xs mt-4 rounded-full h-2" style={{ backgroundColor: "var(--color-bg-sunken)" }}>
                    <div className="rounded-full h-2 transition-all" style={{ backgroundColor: "var(--color-accent)", width: `${(batchProgress / batchEmails.length) * 100}%` }} />
                  </div>
                )}
              </motion.div>
            )}

            {/* BATCH RESULTS */}
            {batchResults.length > 0 && !isAnalyzing && (
              <motion.div key="batch" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} className="space-y-4">
                <div className="rounded-2xl border p-5" style={{ backgroundColor: "var(--color-bg-elevated)" }}>
                  <p className="text-xs font-mono uppercase tracking-wide mb-3" style={{ color: "var(--color-text-tertiary)" }}>
                    Batch analysis — {batchResults.length} emails
                  </p>
                  <div className="flex gap-4">
                    <div className="text-center">
                      <p className="text-xl font-bold font-mono" style={{ color: "var(--color-risk-high)" }}>{highCount}</p>
                      <p className="text-[10px] font-mono" style={{ color: "var(--color-text-tertiary)" }}>High</p>
                    </div>
                    <div className="text-center">
                      <p className="text-xl font-bold font-mono" style={{ color: "var(--color-risk-medium)" }}>{medCount}</p>
                      <p className="text-[10px] font-mono" style={{ color: "var(--color-text-tertiary)" }}>Medium</p>
                    </div>
                    <div className="text-center">
                      <p className="text-xl font-bold font-mono" style={{ color: "var(--color-risk-low)" }}>{lowCount}</p>
                      <p className="text-[10px] font-mono" style={{ color: "var(--color-text-tertiary)" }}>Low</p>
                    </div>
                  </div>
                </div>

                <div className="rounded-2xl border divide-y" style={{ backgroundColor: "var(--color-bg-elevated)" }}>
                  {batchResults.map((r, i) => (
                    <div key={i}>
                      <button
                        type="button"
                        onClick={() => setExpandedBatch(expandedBatch === i ? null : i)}
                        className="w-full p-4 text-left"
                        style={{ borderLeft: r.riskTier === "High" ? "4px solid var(--color-risk-high)" : r.riskTier === "Medium" ? "4px solid var(--color-risk-medium)" : "4px solid var(--color-risk-low)" }}
                      >
                        <div className="flex items-center justify-between gap-3">
                          <div className="min-w-0 flex-1">
                            <div className="flex items-center gap-2">
                              <span className="text-[11px] font-mono font-semibold" style={{ color: "var(--color-accent)" }}>#{i + 1}</span>
                              <p className="text-sm font-medium truncate" style={{ color: "var(--color-text-primary)" }}>
                                {r.sender || batchEmails[i]?.sender || "Unknown sender"}
                              </p>
                            </div>
                            <p className="text-xs mt-0.5 truncate" style={{ color: "var(--color-text-secondary)" }}>
                              {r._originalBody?.slice(0, 100)}...
                            </p>
                          </div>
                          <div className="flex items-center gap-2 shrink-0">
                            <RiskBadge tier={r.riskTier} score={r.riskScore} size="sm" />
                            {expandedBatch === i ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                          </div>
                        </div>
                      </button>
                      {expandedBatch === i && !r._error && (
                        <div className="px-4 pb-4">
                          <SingleResult result={r} emailText={r._originalBody} />
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </motion.div>
            )}

            {/* SINGLE RESULT */}
            {result && !isAnalyzing && batchResults.length === 0 && (
              <motion.div key="result" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}>
                <SingleResult result={result} emailText={emailText} />
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
      )} {/* end paste tab */}

      {/* ── GMAIL TAB ──────────────────────────────────────────── */}
      {activeTab === "gmail" && (
        <div className="grid gap-6 lg:grid-cols-[380px_1fr] lg:items-start">
          {/* Left: connect panel */}
          <div className="space-y-4">
            <GmailConnect onStatusChange={setGmailConnected} />
            {!gmailConnected && (
              <div
                className="rounded-2xl border p-4 text-xs leading-relaxed space-y-2"
                style={{ backgroundColor: "var(--color-bg-elevated)", color: "var(--color-text-secondary)" }}
              >
                <p className="font-semibold" style={{ color: "var(--color-text-primary)" }}>How it works</p>
                <p>1. Click <strong>Connect Gmail</strong> — you'll be taken to Google's consent page.</p>
                <p>2. Grant read-only access. PsychShield cannot send, delete, or modify any emails.</p>
                <p>3. Return here and click <strong>Scan Inbox</strong> to run the full detection pipeline on your recent emails.</p>
                <p>4. Results are sorted by risk score and saved to your Dashboard.</p>
                <p className="pt-1" style={{ color: "var(--color-text-tertiary)" }}>
                  Requires a Google Cloud project with the Gmail API enabled and your redirect URI registered.
                  Set <code>GOOGLE_CLIENT_ID</code> and <code>GOOGLE_CLIENT_SECRET</code> in <code>backend/.env</code>.
                </p>
              </div>
            )}
          </div>

          {/* Right: scan panel (only when connected) */}
          <div>
            {gmailConnected
              ? <GmailScanPanel />
              : (
                <div
                  className="flex h-64 items-center justify-center rounded-2xl border border-dashed"
                  style={{ borderColor: "var(--color-border)" }}
                >
                  <p className="text-sm" style={{ color: "var(--color-text-tertiary)" }}>
                    Connect Gmail to start scanning your inbox.
                  </p>
                </div>
              )
            }
          </div>
        </div>
      )} {/* end gmail tab */}
    </div>
  );
}
