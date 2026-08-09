"""Generates N sample emails matching the schema in spec §3.1, for anyone
trying the frontend without their own inbox.json. Deliberately includes
a spread across all 12 worked-example archetypes so the demo actually
exercises every routing path, not just easy cases.
"""
import random
from datetime import datetime, timedelta

ARCHETYPES = [
    dict(subject="RFP - Enterprise Document Management System",
         body="Dear Team,\n\nPlease find attached our RFP for a document management system covering "
              "4 plants and ~1,200 users. Indicative budget is Rs. 25 lakhs. Proposals must reach us "
              "by 12th August 2026.\n\nRegards,\n{from_name}",
         from_name="Suresh Kulkarni", from_email="s.kulkarni@meridiansteel.co.in", company="Meridian Steel"),
    dict(subject="Quick demo request",
         body="Hi, we're a 30-person logistics startup in Pune. Can we get a demo sometime next week? "
              "Nothing urgent.\n\n{from_name}, Founder",
         from_name="Ankit Bose", from_email="ankit@railyardlogistics.in", company="Railyard Logistics"),
    dict(subject="Tender Notice BHEL/PROC/2026/0847",
         body="Bharat Heavy Electricals Limited invites bids for supply of analytics software licences. "
              "Estimated value: Rs. 6,50,000. Last date for bid submission: 03-08-2026, 1700 hrs IST.",
         from_name="BHEL Procurement", from_email="procurement@bhel.gov.in", company="Bharat Heavy Electricals Limited"),
    dict(subject="Sponsorship confirmation needed",
         body="We're finalising sponsors for the India SaaS Summit in Bengaluru. Gold tier is Rs. 4,00,000 "
              "and includes a keynote slot. We need confirmation by tomorrow EOD.\n\n{from_name}, Sponsorship Lead",
         from_name="Nandita Reddy", from_email="nandita@saassummit.in", company="India SaaS Summit"),
    dict(subject="Invoice INV-2026-0331",
         body="Please find attached invoice INV-2026-0331 for Rs. 1,18,000 (incl. 18% GST) against "
              "PO-88214. This is now 12 days overdue.",
         from_name="Accounts", from_email="accounts@vantagecloud.in", company="Vantage Cloud Services"),
    dict(subject="Partnership / reseller enquiry",
         body="We're a Salesforce implementation partner across MEA with 40+ enterprise clients. "
              "We'd like to explore reselling your platform, or a technical integration at minimum.",
         from_name="Zenith Partners", from_email="partnerships@zenithcloud.com", company="Zenith Cloud Partners"),
    dict(subject="Out of Office",
         body="I am out of office until 14th August with limited access to email. For urgent matters "
              "contact my colleague. Sent from Outlook.",
         from_name="Auto Reply", from_email="s.kulkarni@meridiansteel.co.in", company=None),
    dict(subject="Quick question about your SEO",
         body="Hi, I noticed your website isn't ranking on page 1. We've helped 200+ SaaS companies "
              "3x their organic traffic with content marketing, PR outreach, and webinar promotion. "
              "Free audit attached — interested in a 15 min call?",
         from_name="Growth Agency", from_email="hello@rankboost.io", company=None),
    dict(subject="The B2B Growth Weekly — Issue #212",
         body="In this edition: why PLG is stalling, 5 pricing experiments that worked. [Unsubscribe]",
         from_name="B2B Growth Weekly", from_email="newsletter@b2bgrowth.com", company=None),
    dict(subject="Booth follow-up — two things",
         body="Hi — we met at your booth in Mumbai. (1) we'd like to evaluate your platform for our "
              "800-person org, budget TBD, and (2) our CMO wants to co-host a webinar in September. "
              "Can you loop in the right people?\n\n{from_name}, VP Strategy",
         from_name="Farhan Qureshi", from_email="farhan@halcyonretail.in", company="Halcyon Retail"),
    dict(subject="Dealer network product enquiry",
         body="Bhai, humko aapka product chahiye for our dealer network. Around 150 users honge. "
              "Budget approx 1.2 cr allocated hai for this FY. Board review 20th ko hai.",
         from_name="Rajesh Gupta", from_email="rajesh@tradehub.in", company=None),
]


def generate(n: int = 250, seed: int = 42) -> list:
    random.seed(seed)
    base_time = datetime(2026, 8, 1, 9, 0)
    emails = []
    for i in range(n):
        archetype = random.choice(ARCHETYPES)
        received = base_time + timedelta(hours=random.randint(0, 24 * 10), minutes=random.randint(0, 59))
        thread_id = f"th_{(i // 3):04d}"  # occasional shared threads to exercise reconciliation
        emails.append({
            "email_id": f"em_{i:05d}",
            "thread_id": thread_id,
            "message_index": i % 3,
            "from_name": archetype["from_name"],
            "from_email": archetype["from_email"],
            "to": "sales@company.com",
            "cc": [],
            "subject": archetype["subject"],
            "body": archetype["body"].format(from_name=archetype["from_name"]),
            "received_at": received.strftime("%Y-%m-%dT%H:%M:%S+05:30"),
            "attachments": [],
            "is_reply": i % 3 != 0,
        })
    return emails


if __name__ == "__main__":
    import json
    print(json.dumps(generate(250), indent=2))