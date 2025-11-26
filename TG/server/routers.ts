import { COOKIE_NAME } from "@shared/const";
import { getSessionCookieOptions } from "./_core/cookies";
import { systemRouter } from "./_core/systemRouter";
import { publicProcedure, router } from "./_core/trpc";
import { logRedirect, updateRedirect, getCampaignStats, upsertCampaign } from "./db";

export const appRouter = router({
    // if you need to use socket.io, read and register route in server/_core/index.ts, all api should start with '/api/' so that the gateway can route correctly
  system: systemRouter,
  auth: router({
    me: publicProcedure.query(opts => opts.ctx.user),
    logout: publicProcedure.mutation(({ ctx }) => {
      const cookieOptions = getSessionCookieOptions(ctx.req);
      ctx.res.clearCookie(COOKIE_NAME, { ...cookieOptions, maxAge: -1 });
      return {
        success: true,
      } as const;
    }),
  }),

  redirect: router({
    /**
     * Log a user visit to the landing page.
     * This is called from the frontend landing page to track user interactions.
     */
    logVisit: publicProcedure
      .input((data: unknown) => {
        const obj = data as Record<string, unknown>;
        return {
          visitorId: String(obj.visitorId || ""),
          targetUrl: String(obj.targetUrl || ""),
          userAgent: String(obj.userAgent || ""),
          referer: String(obj.referer || ""),
          ipAddress: String(obj.ipAddress || ""),
          deviceType: String(obj.deviceType || ""),
          country: String(obj.country || ""),
        };
      })
      .mutation(async ({ input }) => {
        try {
          await logRedirect({
            visitorId: input.visitorId,
            targetUrl: input.targetUrl,
            userAgent: input.userAgent,
            referer: input.referer,
            ipAddress: input.ipAddress,
            deviceType: input.deviceType,
            country: input.country,
            redirected: 0,
          });
          return { success: true };
        } catch (error) {
          console.error("Failed to log visit:", error);
          return { success: false, error: String(error) };
        }
      }),

    /**
     * Mark a user as redirected.
     */
    markRedirected: publicProcedure
      .input((data: unknown) => {
        const obj = data as Record<string, unknown>;
        return {
          visitorId: String(obj.visitorId || ""),
          redirectTime: Number(obj.redirectTime || 0),
          sessionDuration: Number(obj.sessionDuration || 0),
        };
      })
      .mutation(async ({ input }) => {
        try {
          await updateRedirect(input.visitorId, {
            redirected: 1,
            redirectTime: input.redirectTime,
            sessionDuration: input.sessionDuration,
          });
          return { success: true };
        } catch (error) {
          console.error("Failed to mark redirected:", error);
          return { success: false, error: String(error) };
        }
      }),

    /**
     * Get campaign statistics (admin only).
     */
    getCampaignStats: publicProcedure
      .input((data: unknown) => {
        const obj = data as Record<string, unknown>;
        return { campaignId: String(obj.campaignId || "") };
      })
      .query(async ({ input }) => {
        try {
          const stats = await getCampaignStats(input.campaignId);
          return stats;
        } catch (error) {
          console.error("Failed to get campaign stats:", error);
          return null;
        }
      }),

    /**
     * Create or update a campaign (admin only).
     */
    upsertCampaign: publicProcedure
      .input((data: unknown) => {
        const obj = data as Record<string, unknown>;
        return {
          campaignId: String(obj.campaignId || ""),
          campaignName: String(obj.campaignName || ""),
          targetUrl: String(obj.targetUrl || ""),
          landingPageUrl: String(obj.landingPageUrl || ""),
          active: Number(obj.active || 1),
          conversionGoal: String(obj.conversionGoal || ""),
          trackingEnabled: Number(obj.trackingEnabled || 1),
        };
      })
      .mutation(async ({ input }) => {
        try {
          await upsertCampaign({
            campaignId: input.campaignId,
            campaignName: input.campaignName,
            targetUrl: input.targetUrl,
            landingPageUrl: input.landingPageUrl,
            active: input.active,
            conversionGoal: input.conversionGoal,
            trackingEnabled: input.trackingEnabled,
            totalVisits: 0,
            totalRedirects: 0,
          });
          return { success: true };
        } catch (error) {
          console.error("Failed to upsert campaign:", error);
          return { success: false, error: String(error) };
        }
      }),
  }),

  // TODO: add feature routers here, e.g.
  // todo: router({
  //   list: protectedProcedure.query(({ ctx }) =>
  //     db.getUserTodos(ctx.user.id)
  //   ),
  // }),
});

export type AppRouter = typeof appRouter;
