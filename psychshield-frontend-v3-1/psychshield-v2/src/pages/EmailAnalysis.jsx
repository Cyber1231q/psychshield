import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ScanLine, Loader2, Link2, ShieldAlert, Brain, FileText, Upload, Mail, AlertTriangle, ChevronDown, ChevronUp } from "lucide-react";
import TriggerMap from "../components/triggers/TriggerMap";
import RiskBadge from "../components/ui/RiskBadge";
import SenderVerification from "../components/ui/SenderVerification";
import PreClickWarning from "../components/ui/PreClickWarning";
import { api } from "../lib/api";
import ScrollReveal from "../components/ui/ScrollReveal";

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
            body: batchEmails[i].body,
            sender: batchEmails[i].sender || undefined,
          });
          results.push({ ...data, _index: i, _originalBody: batchEmails[i].body });
        } catch (err) {
          results.push({ _index: i, _error: true, _originalBody: batchEmails[i].body, riskScore: 0, riskTier: "Error" });
        }
      }
      setBatchResults(results);
    } else {
      try {
        const data = await api.analyzeEmail({ body: emailText, sender: senderEmail || undefined });
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
    const docXml = await zip.file("word/document.xml")?.async("string");
    if (!docXml) throw new Error("No document.xml found");
    return docXml.replace(/<[^>]+>/g, " ").replace(/\s+/g, " ").trim();
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

    const name = file.name.toLowerCase();

    if (name.endsWith(".docx")) {
      try {
        const text = await extractDocxText(file);
        if (!text) { setUploadError("Could not extract text from this .docx file."); return; }
        processFileText(text);
      } catch {
        setUploadError("Failed to read .docx file. Try saving as .txt instead.");
      }
      e.target.value = "";
      return;
    }

    const allowed = [".eml", ".txt", ".msg", ".mbox"];
    if (!allowed.some((ext) => name.endsWith(ext))) {
      setUploadError(`Unsupported file type. Upload .eml, .txt, or .docx files. Received: .${name.split(".").pop()}`);
      e.target.value = "";
      return;
    }

    const reader = new FileReader();
    reader.onload = (ev) => {
      const raw = ev.target.result;
      if (/[\x00-\x08\x0E-\x1F]/.test(raw.slice(0, 500))) {
        setUploadError("This file contains binary data. Please paste the email text directly or save as .txt first.");
        return;
      }
      processFileText(raw);
    };
    reader.readAsText(file);
  }

  const highCount = batchResults.filter((r) => r.riskTier === "High").length;
  const medCount = batchResults.filter((r) => r.riskTier === "Medium").length;
  const lowCount = batchResults.filter((r) => r.riskTier === "Low").length;

  return (
    <div className="mx-auto max-w-6xl px-6 py-12">
      <div className="mb-8">
        <p className="text-xs font-mono uppercase tracking-wide" style={{ color: "var(--color-accent)" }}>Analysis interface</p>
        <h1 className="mt-2 text-3xl font-bold tracking-tight" style={{ color: "var(--color-text-primary)" }}>
          Decompose an email before you act on it
        </h1>
        <p className="mt-2 max-w-2xl text-sm" style={{ color: "var(--color-text-secondary)" }}>
          Paste email content or upload a file. Files with multiple emails are automatically split and analyzed individually.
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-[1fr_1fr] lg:items-start">
        {/* INPUT PANEL */}
        <div className="rounded-2xl border p-5" style={{ backgroundColor: "var(--color-bg-elevated)" }}>
          <div className="flex items-center justify-between gap-2 mb-3">
            <div className="flex items-center gap-2">
              <FileText size={15} style={{ color: "var(--color-text-tertiary)" }} />
              <span className="text-xs font-mono" style={{ color: "var(--color-text-tertiary)" }}>email_body.txt / .eml / .docx</span>
            </div>
            <label className="focus-ring inline-flex cursor-pointer items-center gap-1.5 rounded-md border px-3 py-1.5 text-xs font-medium transition-colors hover:opacity-80" style={{ borderColor: "var(--color-border-strong)", color: "var(--color-text-secondary)" }}>
              <Upload size={12} />
              Upload file
              <input type="file" accept=".eml,.txt,.docx,message/rfc822" className="sr-only" onChange={handleFileUpload} />
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
    </div>
  );
}
