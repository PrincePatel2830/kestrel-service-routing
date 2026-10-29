KESTREL HOME — SERVICE ROUTING DATA PACK (Variant B)
====================================================

train.csv             Past service requests.
test_unlabelled.csv   The most recent requests, same columns without team_label.
  request_id          Service request number
  created_at_ist      Creation time (IST)
  channel             ivr | chat | whatsapp | email
  product_family      Product the request is about
  warranty_status     in_warranty | shield | out_of_warranty
  request_text        Customer's opening message (chat/whatsapp/email) or IVR transcript
  source              crm | legacy_zoho (before 1 Oct 2025)
  team_label          Queue assigned by the vendor routing bot at creation (train only)

resolution_log.csv    One row per train request: first_team, final_team (team that closed it),
                      transfers, resolved_at
teams.csv             team, renamed_to, handles
sample_submission.csv request_id, team
ops-policy.pdf        Kestrel operations policy v4.1 — routing rules, costs, team changes, systems.
email-thread.txt      Messages already exchanged about this work.

No other documentation is available.
