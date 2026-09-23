import { EventSchemas, Inngest } from "inngest";

import type { ScanSubmittedData } from "../types.js";

type Events = {
  "scan.submitted": { data: ScanSubmittedData };
};

export const inngest = new Inngest({
  id: "gigantic-journeys",
  schemas: new EventSchemas().fromRecord<Events>(),
});
