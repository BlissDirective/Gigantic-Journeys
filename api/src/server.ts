import { createServer } from "node:http";

import { serve } from "inngest/node";

import { inngest } from "./inngest/client.js";
import { functions } from "./inngest/functions.js";

// Local-dev serve endpoint so `inngest-cli dev` can discover the function.
// Not deployed in M0 (see README: Vercel/Inngest deploy waits on their AUTHs).
const port = Number(process.env.PORT ?? 3000);
const handler = serve({ client: inngest, functions });

createServer(handler).listen(port, () => {
  console.log(`Inngest endpoint on http://localhost:${port}/api/inngest`);
});
