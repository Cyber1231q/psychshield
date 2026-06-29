/**
 * Mock data shaped exactly like the FastAPI backend's expected
 * response schema, so swapping mock calls for real `api.*` calls
 * later requires no component changes.
 *
 * Shape mirrors: Emails, AnalysisResults, URLFlags, AuditLog
 * (Data Layer entities in the System Architecture diagram).
 */

export const TRIGGER_META = {
  urgency: { label: "Urgency", colorVar: "--color-trigger-urgency" },
  fear: { label: "Fear", colorVar: "--color-trigger-fear" },
  authority: { label: "Authority", colorVar: "--color-trigger-authority" },
  trust: { label: "Trust", colorVar: "--color-trigger-trust" },
  pity: { label: "Pity", colorVar: "--color-trigger-pity" },
};

export const mockEmails = [
  {
    id: "em_8841",
    subject: "URGENT: Your account will be suspended in 2 hours",
    sender: "security-alert@paypa1-support.com",
    receivedAt: "2026-06-17T08:12:00Z",
    riskScore: 91,
    riskTier: "High",
    snippet: "We have detected unusual activity. Failure to verify within 2 hours will result in permanent suspension...",
  },
  {
    id: "em_8839",
    subject: "Re: Invoice #4471 — action required from Finance",
    sender: "j.morrison@vendor-billing-co.net",
    receivedAt: "2026-06-17T07:45:00Z",
    riskScore: 74,
    riskTier: "High",
    snippet: "As discussed, please process this wire transfer before end of day to avoid late penalties...",
  },
  {
    id: "em_8835",
    subject: "Your colleague shared a document with you",
    sender: "notifications@docu-share-cloud.com",
    receivedAt: "2026-06-16T19:20:00Z",
    riskScore: 58,
    riskTier: "Medium",
    snippet: "Sarah from HR shared 'Q3_Compensation_Review.pdf' with you. Click below to view...",
  },
  {
    id: "em_8830",
    subject: "Team lunch next Thursday?",
    sender: "amaka.okafor@calebuniversity.edu.ng",
    receivedAt: "2026-06-16T14:02:00Z",
    riskScore: 6,
    riskTier: "Low",
    snippet: "Hey team, thinking of booking the usual spot for lunch next Thursday. Let me know if that works...",
  },
  {
    id: "em_8827",
    subject: "IT Security: Mandatory password reset",
    sender: "it-helpdesk@caleb-university-portal.com",
    receivedAt: "2026-06-16T11:30:00Z",
    riskScore: 83,
    riskTier: "High",
    snippet: "Due to a recent security incident, all staff must reset their passwords within 24 hours using the link below...",
  },
  {
    id: "em_8819",
    subject: "Your subscription receipt",
    sender: "billing@notion.so",
    receivedAt: "2026-06-15T09:15:00Z",
    riskScore: 12,
    riskTier: "Low",
    snippet: "Thanks for your payment. Here's your receipt for the Notion Plus plan, billed monthly...",
  },
];

export const mockAnalysisResult = {
  id: "em_8841",
  subject: "URGENT: Your account will be suspended in 2 hours",
  sender: "security-alert@paypa1-support.com",
  receivedAt: "2026-06-17T08:12:00Z",
  riskScore: 91,
  riskTier: "High",
  bodyPreview:
    "Dear Customer, We have detected unusual activity on your account. For your security, access has been temporarily limited. Failure to verify your identity within 2 hours will result in permanent suspension of your account. Click the link below immediately to restore full access. This is your final notice.",

  emotionDetection: {
    model: "GoEmotions + TF-IDF/SVM",
    categoryScores: [
      { category: "fear", score: 0.82 },
      { category: "urgency", score: 0.91 },
      { category: "neutral", score: 0.06 },
      { category: "trust", score: 0.11 },
    ],
    emotionScore: 0.88,
    summary: "Strong fear and urgency signals consistent with account-suspension scare tactics.",
  },

  manipulationPattern: {
    model: "Regex + Naive Bayes",
    patternScore: 0.86,
    techniques: [
      { name: "Artificial time pressure", evidence: "\"within 2 hours\"" },
      { name: "Threat of loss", evidence: "\"permanent suspension\"" },
      { name: "Authority impersonation", evidence: "\"Dear Customer\" generic greeting from a brand name" },
      { name: "Call-to-action urgency", evidence: "\"Click the link below immediately\"" },
    ],
  },

  linkVerification: {
    model: "PhishTank API + LegitPhish DB + Structural Analysis",
    linkScore: 0.94,
    urls: [
      {
        url: "hxxps://paypa1-support.com/verify-account",
        flags: ["Typosquatted domain (paypa1 vs paypal)", "Not in LegitPhish trusted list", "Flagged on PhishTank"],
        riskLevel: "High",
      },
    ],
  },

  triggers: {
    urgency: 91,
    fear: 82,
    authority: 64,
    trust: 11,
    pity: 4,
  },

  riskReport: {
    weightedFormula: "0.35×Emotion + 0.30×Manipulation + 0.35×LinkThreat",
    finalScore: 91,
    tier: "High",
    explanation:
      "This email combines high fear and urgency language with a typosquatted sender domain flagged by PhishTank. The combination of psychological pressure and a deceptive link is the strongest predictor of social engineering in the training data.",
  },

  // Sender verification — extracted by backend pre-processing pipeline
  senderVerification: {
    from: "security-alert@paypa1-support.com",
    displayName: "PayPal Security",
    replyTo: "harvest@randomdomain.net",
    domain: "paypa1-support.com",
    typosquatted: true,
    spf: "FAIL",
    dkim: "FAIL",
    dmarc: "FAIL",
    domainAgeDays: 3,
  },
};

export const mockAnalytics = {
  totalAnalyzed: 4218,
  highRisk: 612,
  mediumRisk: 891,
  lowRisk: 2715,
  detectionRateTrend: [
    { date: "Jun 11", high: 18, medium: 24, low: 71 },
    { date: "Jun 12", high: 22, medium: 31, low: 68 },
    { date: "Jun 13", high: 15, medium: 27, low: 80 },
    { date: "Jun 14", high: 29, medium: 22, low: 74 },
    { date: "Jun 15", high: 24, medium: 35, low: 69 },
    { date: "Jun 16", high: 31, medium: 28, low: 77 },
    { date: "Jun 17", high: 19, medium: 30, low: 82 },
  ],
  topTriggers: [
    { trigger: "Urgency", count: 1842 },
    { trigger: "Fear", count: 1390 },
    { trigger: "Authority", count: 1024 },
    { trigger: "Trust", count: 588 },
    { trigger: "Pity", count: 301 },
  ],
};

export const mockAuditLog = [
  { id: "log_001", timestamp: "2026-06-17T08:12:05Z", actor: "system", action: "Email em_8841 classified High risk (score 91)" },
  { id: "log_002", timestamp: "2026-06-17T08:10:44Z", actor: "admin@calebuniversity.edu.ng", action: "Updated risk threshold for Medium tier from 40 to 45" },
  { id: "log_003", timestamp: "2026-06-16T19:20:12Z", actor: "system", action: "Email em_8835 classified Medium risk (score 58)" },
  { id: "log_004", timestamp: "2026-06-16T11:31:02Z", actor: "system", action: "Email em_8827 classified High risk (score 83)" },
  { id: "log_005", timestamp: "2026-06-16T09:00:00Z", actor: "admin@calebuniversity.edu.ng", action: "Exported weekly risk report (PDF)" },
];

export const mockUsers = [
  { id: "usr_001", name: "System Administrator", email: "admin@calebuniversity.edu.ng", role: "admin", lastLogin: "2026-06-17T08:00:00Z", status: "active" },
  { id: "usr_002", name: "Security Analyst", email: "analyst@calebuniversity.edu.ng", role: "analyst", lastLogin: "2026-06-17T07:30:00Z", status: "active" },
  { id: "usr_003", name: "IT Officer", email: "it@calebuniversity.edu.ng", role: "analyst", lastLogin: "2026-06-16T15:10:00Z", status: "active" },
];

export const mockModelMetrics = {
  accuracy: 91.4,
  highRecall: 93.2,
  precision: 89.7,
  f1Score: 91.4,
  avgLatencyMs: 1240,
  lastEvaluated: "2026-06-17T06:00:00Z",
};
