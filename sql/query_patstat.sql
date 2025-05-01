SELECT  CONCAT(a.appln_auth, a.appln_nr, a.appln_kind) AS numsol,
        CONCAT(p.publn_auth, p.publn_nr, p.publn_kind) AS publication,
        t.appln_title, STRING_AGG(CAST(pe.person_name AS VARCHAR(MAX)), '|') AS applicants,
        f.fam_publn_auth, f.fam_publn_nr, f.fam_publn_kind
FROM tls201_appln AS a
JOIN tls211_pat_publn AS p ON a.appln_id = p.appln_id
LEFT JOIN tls202_appln_title AS t ON a.appln_id = t.appln_id
LEFT JOIN tls207_pers_appln AS pa ON a.appln_id = pa.appln_id
LEFT JOIN tls206_person AS pe ON pa.person_id = pe.person_id
LEFT JOIN ( SELECT t1.*,t3.publn_auth AS fam_publn_auth, t3.publn_nr AS fam_publn_nr, 
                    t3.publn_kind AS fam_publn_kind
            FROM tls228_docdb_fam_citn AS t1
            INNER JOIN tls201_appln AS t2 ON t1.docdb_family_id = t2.docdb_family_id
            INNER JOIN tls211_pat_publn AS t3 ON t2.appln_id = t3.appln_id
            WHERE t3.publn_auth in ('ES','MX','WO')
        ) AS f ON a.docdb_family_id = f.docdb_family_id
WHERE appln_auth = 'PE' 
    AND pa.applt_seq_nr > 0 
    AND appln_nr  in (SELECT doc_number FROM patentes)
GROUP BY a.appln_auth, a.appln_nr, a.appln_kind, p.publn_auth, p.publn_nr, p.publn_kind, 
        t.appln_title,f.fam_publn_auth, f.fam_publn_nr, f.fam_publn_kind;