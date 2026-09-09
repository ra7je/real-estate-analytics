\# Real Estate Analytics Platform



\## Overview



An end-to-end real estate analytics platform built using Snowflake, AWS S3, Snowpipe and Streamlit.



\## Architecture



AWS S3

→ Snowpipe

→ Snowflake RAW

→ Snowflake DW

→ Semantic Layer

→ Streamlit Dashboard



\## Key Components



\- AWS S3 for file landing

\- Snowpipe for automated ingestion

\- Snowflake RAW layer

\- Snowflake dimensional warehouse

\- SCD Type 2 dimensions

\- Incremental processing using Snowflake Streams and Tasks

\- Semantic analytics views

\- Streamlit executive dashboard

\- Data quality and operational monitoring



\## Dashboard



The dashboard provides:



\- Executive Summary

\- City Insights

\- Developer Performance

\- Property Explorer

\- Date and business-dimension filters

\- Sales trend analysis

\- Developer and city performance

\- Property-level exploration



\## Security



Credentials, secrets, environment files and local data files are excluded from Git using `.gitignore`.



\## Technology Stack



\- Snowflake

\- AWS S3

\- Snowpipe

\- Snowflake Streams

\- Snowflake Tasks

\- SQL

\- Python

\- Streamlit

\- Altair

