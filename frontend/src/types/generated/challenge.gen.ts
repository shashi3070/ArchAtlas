/**
 * Progressive-chain membership (e.g. url-shortener level 2 of 6).
 */
export type ChainLink = {
  family_id?: string;
  level?: number;
  next_challenge_id?: string | null;
} | null;

/**
 * A learning challenge definition (authored in YAML, validated with this schema). Shape follows SYSTEM.md section 25.
 */
export interface Challenge {
  id: string;
  title: string;
  difficulty: "beginner" | "intermediate" | "advanced" | "expert";
  /**
   * Learning mode this challenge runs in.
   */
  mode?: "challenge" | "repair" | "explore" | "interview";
  /**
   * Fictional-company scenario framing.
   */
  narrative?: string | null;
  requirements?: ChallengeRequirement[];
  constraints?: ChallengeConstraint[];
  learning_objectives?: string[];
  /**
   * Palette restriction; empty/omitted means full catalog.
   */
  allowed_components?: string[];
  /**
   * Subset of rule ids active for scoring this challenge.
   */
  evaluation_rules?: string[];
  /**
   * Chaos/scenario event ids playable within this challenge (Phase 8 hooks).
   */
  scenarios?: string[];
  /**
   * Optional golden architecture used as the starting canvas (required for repair drills).
   */
  starting_graph_ref?: string | null;
  /**
   * Ordered hint ladder: nudge -> concept -> partial structure -> full rationale.
   */
  hints?: string[];
  /**
   * Extra context injected into tutor/coach prompts for this challenge.
   */
  ai_context_notes?: string | null;
  chain?: ChainLink;
  related_topics?: string[];
  version?: string;
}
export interface ChallengeRequirement {
  id: string;
  category:
    "functional" | "scale" | "performance" | "availability" | "consistency" | "durability" | "security" | "cost";
  description: string;
  metric?: string | null;
  value?: number | string | null;
  unit?: string | null;
  priority?: "must" | "should" | "could";
}
export interface ChallengeConstraint {
  key: string;
  value: {
    [k: string]: unknown;
  };
  severity?: "hard" | "soft";
}
