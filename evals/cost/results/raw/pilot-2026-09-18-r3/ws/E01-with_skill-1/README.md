# cost-app

A small but real web application used as the execution substrate for the
Stage 2 cost baseline. Tasks are run against this repo so that repository
exploration, file edits and tool loops are actually exercised — a cost
measurement taken in an empty directory would miss them entirely.

What is here: a homepage, an order list, an order form, a products API,
an orders API, a session helper, a SQL schema, a theme and an i18n bundle.

How to run: `npm install && npm run dev` (standard scripts, no build step
required to read or edit the sources).

Deliberately NOT here: any description of what is wrong with the code, any
grading criteria, any hint about which task targets which file. Those live
in the eval cases under `evals/`. A fixture that names the defect turns the
run into dictation instead of engineering.
