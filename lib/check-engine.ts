export type CheckStatus =
  | "Green - Aligned"
  | "Yellow - Discern"
  | "Blue - Needs Counsel"
  | "Red - Hold as Written"
  | "Grey - Need More Context"

export type CheckResult = {
  status: CheckStatus
  guidance: string
  bibleSays: string
  jesusTeaches: string
  mainReason: string
  oneStep: string
  meaning: string[]
  references: string[]
  flags: string[]
  crisis: boolean
}

type Rule = {
  label: string
  patterns: RegExp[]
}

const crisisRules: Rule[] = [
  {
    label: "possible immediate crisis",
    patterns: [
      /\b(kill myself|suicide|end my life|hurt myself|harm myself)\b/i,
      /\b(don't want to be here|do not want to be here|want it to end)\b/i,
      /\b(immediate danger|being abused|someone is hurting me)\b/i,
    ],
  },
]

const redRules: Rule[] = [
  {
    label: "guarantees an outcome God has not universally promised",
    patterns: [
      /\b(god will definitely|god is guaranteed to|guaranteed blessing|guaranteed breakthrough)\b/i,
      /\b(if you believe enough|if your faith is strong enough).*\b(heal|rich|money|breakthrough|success)\b/i,
      /\b(prayer works every time exactly|exactly how i want)\b/i,
    ],
  },
  {
    label: "uses spiritual pressure or manipulation",
    patterns: [
      /\b(if you don't repost|if you do not repost|share this or|repost this or)\b/i,
      /\b(ashamed of jesus|not a real christian|prove you love god)\b/i,
    ],
  },
  {
    label: "claims authority over another person's life",
    patterns: [
      /\bgod told me (you|him|her|them)\b/i,
      /\bgod says (you|him|her|them) (must|need to|have to)\b/i,
      /\byou need to marry\b/i,
    ],
  },
]

const blueRules: Rule[] = [
  {
    label: "public accusation or correction",
    patterns: [
      /\b(false teacher|false prophet|expose|call out|everyone should avoid)\b/i,
      /\bthis pastor|this leader|my pastor|my leader\b/i,
    ],
  },
  {
    label: "sensitive testimony or third-party story",
    patterns: [
      /\b(trauma|abuse|addiction|overdose|assault|molested|rape)\b/i,
      /\b(my child|my kid|my son|my daughter|someone else's story|their private)\b/i,
    ],
  },
  {
    label: "professional or money-sensitive claim",
    patterns: [
      /\b(legal advice|lawsuit|diagnosed|medication|stop taking|investment|donate now|sow a seed)\b/i,
    ],
  },
]

const yellowRules: Rule[] = [
  {
    label: "personal spiritual impression that may need softer wording",
    patterns: [
      /\bi think god\b/i,
      /\bgod may be\b/i,
      /\bi feel like god\b/i,
      /\bthis season\b/i,
    ],
  },
  {
    label: "broad encouragement that could use clearer Scripture anchoring",
    patterns: [
      /\bblessed|breakthrough|purpose|calling|destiny|season|anointed\b/i,
    ],
  },
]

const greenRules: Rule[] = [
  {
    label: "edifying speech",
    patterns: [
      /\b(build people up|give grace|encourage|forgive|love one another|trust him|trust jesus)\b/i,
      /\bjesus is the way|jesus is lord|christ died|cross|resurrection\b/i,
    ],
  },
]

function matches(rules: Rule[], message: string) {
  return rules
    .filter((rule) => rule.patterns.some((pattern) => pattern.test(message)))
    .map((rule) => rule.label)
}

function getGuidance(status: CheckStatus) {
  if (status.startsWith("Green")) return "Keep"
  if (status.startsWith("Yellow")) return "Clarify"
  if (status.startsWith("Blue")) return "Seek Counsel"
  if (status.startsWith("Red")) return "Hold as Written"
  return "Need More Context"
}

export function checkMessage(rawMessage: string): CheckResult {
  const message = rawMessage.trim()

  if (!message) {
    return {
      status: "Grey - Need More Context",
      guidance: "Need More Context",
      bibleSays: "Scripture calls our words to be truthful, gracious, and useful for building up.",
      jesusTeaches: "Jesus teaches us to speak from a heart submitted to God.",
      mainReason: "There is no message to review yet.",
      oneStep: "Paste the exact wording you are considering sharing.",
      meaning: ["A careful review needs actual wording, not just the idea behind it."],
      references: ["Eph. 4:29", "Matt. 12:36-37"],
      flags: [],
      crisis: false,
    }
  }

  const crisisFlags = matches(crisisRules, message)

  if (crisisFlags.length > 0) {
    return {
      status: "Blue - Needs Counsel",
      guidance: "Seek Counsel",
      bibleSays: "Your life matters to God, and you do not have to carry danger or despair alone.",
      jesusTeaches: "Jesus moves toward the hurting with compassion and care.",
      mainReason: "This sounds like it may involve immediate danger or deep crisis.",
      oneStep: "Reach out now to emergency help, a trusted person, or your church.",
      meaning: [
        "If you may be in immediate danger or thinking about harming yourself, please call or text 988 (U.S. and Canada) or contact local emergency services now.",
        "Support is free, confidential, and available 24/7. You matter, and you do not have to carry this alone.",
      ],
      references: ["Ps. 34:18", "Matt. 11:28"],
      flags: crisisFlags,
      crisis: true,
    }
  }

  const redFlags = matches(redRules, message)
  const blueFlags = matches(blueRules, message)
  const yellowFlags = matches(yellowRules, message)
  const greenFlags = matches(greenRules, message)

  let status: CheckStatus = "Grey - Need More Context"
  let mainReason = "The message needs more context before it can be reviewed responsibly."
  let oneStep = "Add the exact post wording and any missing context that changes the meaning."
  let meaning = [
    "The tool can help best when it sees the words as others will read them.",
    "When context is missing, the safer path is to slow down before posting.",
  ]
  let references = ["Prov. 18:13", "Eph. 4:29"]

  if (redFlags.length > 0) {
    status = "Red - Hold as Written"
    mainReason = "This wording appears to overclaim, pressure others, or speak with more certainty than Scripture gives."
    oneStep = "Rewrite it as a humble personal reflection without guarantees or spiritual pressure."
    meaning = [
      "A Red result is not a judgment on your heart; it is a warning about the wording.",
      "The safer move is to remove certainty God has not given, remove pressure on the reader, and keep Christ central.",
      "Grace can still be strong without becoming forceful or controlling.",
    ]
    references = ["Matt. 4:7", "James 4:13-16", "Eph. 4:29"]
  } else if (blueFlags.length > 0) {
    status = "Blue - Needs Counsel"
    mainReason = "This message touches sensitive content that should have wise human eyes before it is public."
    oneStep = "Show it to a mature believer, pastor, counselor, or appropriate professional before posting."
    meaning = [
      "Some messages are not wrong, but they are weighty.",
      "Public correction, trauma, private stories, children, money, medical issues, or legal issues need extra care.",
      "Seeking counsel is not fear; it is wisdom.",
    ]
    references = ["Prov. 11:14", "Prov. 15:22", "Gal. 6:1"]
  } else if (yellowFlags.length > 0) {
    status = "Yellow - Discern"
    mainReason = "The message may be good in direction, but it could be clearer, humbler, or more anchored."
    oneStep = "Soften certainty and add a clear Scripture-shaped anchor."
    meaning = [
      "This may be worth sharing after a little refining.",
      "Try to speak as a witness to what God is teaching you, not as an authority over what God must do.",
      "A humble sentence can carry more light than a dramatic one.",
    ]
    references = ["Mic. 6:8", "Col. 4:6", "Eph. 4:29"]
  } else if (greenFlags.length > 0) {
    status = "Green - Aligned"
    mainReason = "The wording appears Christ-centered, edifying, and low risk."
    oneStep = "Read it once more for humility, then share if your conscience is clear."
    meaning = [
      "This message appears to build up rather than pressure, boast, accuse, or overpromise.",
      "Keep the focus on Jesus and let the post serve people rather than perform for them.",
    ]
    references = ["Eph. 4:29", "John 13:34-35", "Col. 3:17"]
  }

  return {
    status,
    guidance: getGuidance(status),
    bibleSays: "Scripture calls our words to be truthful, gracious, humble, and useful for building others up.",
    jesusTeaches: "Jesus teaches that our words flow from the heart, so speech should be surrendered to God.",
    mainReason,
    oneStep,
    meaning,
    references,
    flags: [...redFlags, ...blueFlags, ...yellowFlags, ...greenFlags],
    crisis: false,
  }
}

export function formatCheckResult(result: CheckResult) {
  if (result.crisis) {
    return [
      "Savior Made CHECK Care Note",
      "",
      ...result.meaning,
      "",
      "Please also reach out to a trusted person in your life or your church.",
    ].join("\n")
  }

  return [
    "Savior Made CHECK Result",
    "",
    `CHECK Status: ${result.status}`,
    `Release Guidance: ${result.guidance}`,
    "",
    `Bible Says: ${result.bibleSays}`,
    `Jesus Teaches: ${result.jesusTeaches}`,
    `Main Reason: ${result.mainReason}`,
    `Suggested One Clean Step: ${result.oneStep}`,
    "",
    "What This Means:",
    ...result.meaning,
    "",
    `Read for Yourself: ${result.references.join("; ")}`,
    "",
    "Please read the full passage yourself in context before using this.",
    "",
    "Savior Made CHECK is a Scripture-conscious message review tool. It is not a pastor, prophet, therapist, doctor, lawyer, financial advisor, crisis service, or replacement for Scripture, prayer, church, wise counsel, or qualified professional help. It reviews the message, not the person.",
  ].join("\n")
}
