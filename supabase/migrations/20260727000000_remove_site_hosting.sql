-- Rollback of the site-hosting experiment: Supabase serves HTML as
-- text/plain on its own domain (anti-phishing), so pages can't render there.
-- The frontend is hosted on Vercel instead; the site/sitepush functions are
-- deployed as inert 410 stubs (the platform has no function delete API).
-- The `site` storage bucket was emptied and deleted via the Storage API
-- (SQL deletes on storage tables are blocked by a platform guard).
drop table if exists site_files;
