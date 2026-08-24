-- El image supabase/postgres ya trae el schema auth más nuevo que GoTrue v2.143.0.
-- GoTrue intenta reaplicar 20221208132122 (id = user_id::text) y falla porque
-- identities.id ya es uuid. Marcamos las migraciones restantes como aplicadas.
INSERT INTO auth.schema_migrations (version) VALUES
    ('20221208132122'),
    ('20221215195500'),
    ('20221215195800'),
    ('20221215195900'),
    ('20230116124310'),
    ('20230116124412'),
    ('20230131181311'),
    ('20230322519590'),
    ('20230402418590'),
    ('20230411005111'),
    ('20230508135423'),
    ('20230523124323'),
    ('20230818113222'),
    ('20230914180801'),
    ('20231027141322'),
    ('20231114161723'),
    ('20231117164230')
ON CONFLICT (version) DO NOTHING;
