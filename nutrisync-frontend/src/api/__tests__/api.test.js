import { describe, expect, it } from "vitest";

import { getErrorMessage } from "../api";

describe("getErrorMessage", () => {
  it("prefers FastAPI detail messages before generic fallbacks", () => {
    expect(
      getErrorMessage(
        {
          response: {
            data: {
              detail: "Image scanning is temporarily unavailable on this device.",
            },
          },
        },
        "Fallback message",
      ),
    ).toBe("Image scanning is temporarily unavailable on this device.");
  });
});
