"""Seeds sample policy data into Azure AI Search on startup."""
import json
import os
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
