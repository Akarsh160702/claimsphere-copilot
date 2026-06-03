"""Seeds sample policy data into Azure AI Search on startup.
Also seeds the in-memory claims store with realistic demo claims so the
dashboard always shows live data immediately after a cold start.
"""
import json
import os
from datetime import datetime, timedelta
import structlog

logger = structlog.get_logger()

POLICIES_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "policies")


async def seed_policies(search_client) -> int:
    """Load policy JSON files and index them into Azure AI Search."""
    count = 0
    try:
        if not os.path.exists(POLICIES_DIR):
            logger.warning("policies_dir_not_found", path=POLICIES_DIR)
            return 0

        policies = []
        for filename in os.listdir(POLICIES_DIR):
            if filename.endswith(".json"):
                filepath = os.path.join(POLICIES_DIR, filename)
                with open(filepath, "r", encoding="utf-8") as f:
                    policy = json.load(f)
                    policy["id"] = policy.get("policy_id", filename.replace(".json", ""))
                    # Flatten nested dicts to strings for AI Search indexing
                    if isinstance(policy.get("coverage_details"), dict):
                        policy["coverage_details"] = json.dumps(policy["coverage_details"])
                    if isinstance(policy.get("exclusions"), list):
                        policy["exclusions"] = " | ".join(policy["exclusions"])
                    policies.append(policy)

        count = await search_client.index_policies_bulk(policies)
        logger.info("policies_seeded", count=count, total=len(policies))
    except Exception as e:
        logger.error("policy_seeding_error", error=str(e))
    return count


def seed_demo_claims(store: dict) -> int:
    """
    Pre-populate the in-memory claims store with realistic demo claims.
    Constructed directly (no LLM calls) so startup is instant.
    The dashboard shows 'Live' mode the moment the app starts.
    """
    from backend.models.claim import (
        ClaimContext, ClaimSubmission, ClaimantInfo, ClaimType,
        ClaimStatus, ClaimPriority, Channel, ValidationResult,
        FraudResult, MissingInfoResult, AdjudicationResult, Decision,
    )

    now = datetime.utcnow()

    SEEDS = [
        # 1 — Health claim, approved, STP
        dict(
            claim_id="CLM-DEMO-001",
            submission=ClaimSubmission(
                policy_id="POL-HEALTH-001",
                claimant=ClaimantInfo(name="Rahul Sharma", email="rahul@demo.com", phone="+91-9876543210"),
                claim_type=ClaimType.HEALTH, claim_amount=42000,
                incident_date="2026-05-10",
                description="Day-care procedure for cataract surgery, Apollo Hospital.",
                channel=Channel.WEB,
            ),
            claim_type=ClaimType.HEALTH, priority=ClaimPriority.MEDIUM,
            status=ClaimStatus.APPROVED,
            created_at=now - timedelta(hours=14),
            validation=ValidationResult(is_valid=True, policy_active=True, claim_type_covered=True,
                within_sum_insured=True, deductible_applicable=True, coverage_amount=37000,
                deductible_amount=5000, confidence=0.97,
                validation_notes="Policy active. Day-care covered. Deductible ₹5,000 applied."),
            fraud=FraudResult(fraud_score=8, risk_level="LOW", flags=[],
                reasoning="No fraud indicators. Low amount, established claimant."),
            missing=MissingInfoResult(has_missing_info=False, missing_fields=[]),
            adjudication=AdjudicationResult(
                decision=Decision.APPROVE, claim_amount=42000, approved_amount=37000,
                deductible_applied=5000, final_payout=37000,
                rationale="Policy active, claim type covered, fraud score low (8/100). Auto-approved.",
                confidence_score=0.96, supporting_evidence=["Policy valid", "Fraud LOW"],
            ),
        ),
        # 2 — Motor claim, approved
        dict(
            claim_id="CLM-DEMO-002",
            submission=ClaimSubmission(
                policy_id="POL-MOTOR-001",
                claimant=ClaimantInfo(name="Priya Nair", email="priya@demo.com", phone="+91-9000012345"),
                claim_type=ClaimType.MOTOR, claim_amount=38500,
                incident_date="2026-05-18",
                description="Minor rear-end collision at OMR Junction. Bumper and taillight replaced.",
                channel=Channel.TEAMS,
            ),
            claim_type=ClaimType.MOTOR, priority=ClaimPriority.MEDIUM,
            status=ClaimStatus.APPROVED,
            created_at=now - timedelta(hours=10),
            validation=ValidationResult(is_valid=True, policy_active=True, claim_type_covered=True,
                within_sum_insured=True, deductible_applicable=True, coverage_amount=36500,
                deductible_amount=2000, confidence=0.95,
                validation_notes="Own damage covered. No exclusions triggered. Deductible ₹2,000."),
            fraud=FraudResult(fraud_score=12, risk_level="LOW", flags=[],
                reasoning="Police report consistent with damage description. No red flags."),
            missing=MissingInfoResult(has_missing_info=False, missing_fields=[]),
            adjudication=AdjudicationResult(
                decision=Decision.APPROVE, claim_amount=38500, approved_amount=36500,
                deductible_applied=2000, final_payout=36500,
                rationale="All documents submitted. Fraud score 12/100. Approved.",
                confidence_score=0.93, supporting_evidence=["FIR present", "Repair estimate validated"],
            ),
        ),
        # 3 — Health claim, escalated (high amount)
        dict(
            claim_id="CLM-DEMO-003",
            submission=ClaimSubmission(
                policy_id="POL-HEALTH-001",
                claimant=ClaimantInfo(name="Amit Verma", email="amit@demo.com", phone="+91-9111111111"),
                claim_type=ClaimType.HEALTH, claim_amount=285000,
                incident_date="2026-05-20",
                description="Cardiac bypass surgery, 12-day ICU stay, Fortis Hospital.",
                channel=Channel.EMAIL,
            ),
            claim_type=ClaimType.HEALTH, priority=ClaimPriority.HIGH,
            status=ClaimStatus.UNDER_REVIEW,
            created_at=now - timedelta(hours=5),
            validation=ValidationResult(is_valid=True, policy_active=True, claim_type_covered=True,
                within_sum_insured=True, deductible_applicable=True, coverage_amount=280000,
                deductible_amount=5000, confidence=0.91),
            fraud=FraudResult(fraud_score=22, risk_level="LOW", flags=[],
                reasoning="High amount but consistent with cardiac surgery costs."),
            missing=MissingInfoResult(has_missing_info=True,
                missing_fields=["Surgeon's operative notes", "Pre-auth approval letter"],
                follow_up_message="Please provide operative notes and pre-auth letter."),
            adjudication=AdjudicationResult(
                decision=Decision.ESCALATE, claim_amount=285000, approved_amount=280000,
                deductible_applied=5000, final_payout=0,
                rationale="High-value claim (>₹1L) requires human review per policy.",
                confidence_score=0.82, escalation_reason="High value — human review required",
            ),
        ),
        # 4 — Property claim, rejected (exclusion hit)
        dict(
            claim_id="CLM-DEMO-004",
            submission=ClaimSubmission(
                policy_id="POL-PROPERTY-001",
                claimant=ClaimantInfo(name="Sunita Rao", email="sunita@demo.com", phone="+91-9222222222"),
                claim_type=ClaimType.PROPERTY, claim_amount=95000,
                incident_date="2026-05-22",
                description="Normal wear and tear damage to roof tiles over several years.",
                channel=Channel.PHONE,
            ),
            claim_type=ClaimType.PROPERTY, priority=ClaimPriority.MEDIUM,
            status=ClaimStatus.REJECTED,
            created_at=now - timedelta(hours=2),
            validation=ValidationResult(is_valid=False, policy_active=True, claim_type_covered=True,
                within_sum_insured=True, deductible_applicable=True, coverage_amount=0,
                deductible_amount=10000, exclusions_hit=["Normal wear and tear"], confidence=0.98),
            fraud=FraudResult(fraud_score=5, risk_level="LOW", flags=[]),
            missing=MissingInfoResult(has_missing_info=False, missing_fields=[]),
            adjudication=AdjudicationResult(
                decision=Decision.REJECT, claim_amount=95000, approved_amount=0,
                deductible_applied=0, final_payout=0,
                rationale="Exclusion applies: 'Normal wear and tear' is explicitly excluded.",
                confidence_score=0.98, rejection_reason="Exclusion: Normal wear and tear",
            ),
        ),
        # 5 — Motor claim, pending info
        dict(
            claim_id="CLM-DEMO-005",
            submission=ClaimSubmission(
                policy_id="POL-MOTOR-001",
                claimant=ClaimantInfo(name="Vikram Singh", email="vikram@demo.com", phone="+91-9333333333"),
                claim_type=ClaimType.MOTOR, claim_amount=67000,
                incident_date="2026-05-25",
                description="Vehicle theft from office parking. FIR filed.",
                channel=Channel.WEB,
            ),
            claim_type=ClaimType.MOTOR, priority=ClaimPriority.HIGH,
            status=ClaimStatus.PENDING_INFO,
            created_at=now - timedelta(minutes=45),
            validation=ValidationResult(is_valid=True, policy_active=True, claim_type_covered=True,
                within_sum_insured=True, deductible_applicable=True, coverage_amount=65000,
                deductible_amount=2000, confidence=0.89),
            fraud=FraudResult(fraud_score=35, risk_level="MEDIUM",
                flags=["No CCTV footage provided", "Claim filed 3 days after incident"],
                reasoning="Theft claims have higher baseline fraud risk."),
            missing=MissingInfoResult(has_missing_info=True,
                missing_fields=["Police FIR copy", "Vehicle registration certificate", "Keys surrender proof"],
                follow_up_message="Please provide FIR copy, RC book, and proof of key surrender."),
            adjudication=AdjudicationResult(
                decision=Decision.ESCALATE, claim_amount=67000, approved_amount=65000,
                deductible_applied=2000, final_payout=0,
                rationale="Missing critical theft documents. Medium fraud score requires human review.",
                confidence_score=0.74, escalation_reason="Missing theft documentation",
            ),
        ),
    ]

    audit_agents = ["RouterAgent", "DocumentAgent", "ValidationAgent",
                    "FraudAgent", "MissingInfoAgent", "AdjudicationAgent"]

    for s in SEEDS:
        ctx = ClaimContext(
            claim_id=s["claim_id"],
            submission=s["submission"],
            claim_type=s["claim_type"],
            priority=s["priority"],
            status=s["status"],
            validation_result=s["validation"],
            fraud_result=s["fraud"],
            missing_info_result=s["missing"],
            adjudication_result=s["adjudication"],
            created_at=s["created_at"],
            updated_at=s["created_at"] + timedelta(seconds=18),
        )
        for ag in audit_agents:
            ctx.add_audit(ag, "DEMO_SEED", {"note": "pre-seeded demo claim"})
        store[ctx.claim_id] = ctx

    logger.info("demo_claims_seeded", count=len(SEEDS))
    return len(SEEDS)
