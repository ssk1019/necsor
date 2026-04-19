/**
 * 市場資料 API 呼叫封裝。
 */

export interface InstitutionalItem {
  name: string;
  buy: number;
  sell: number;
  diff: number;
}

export interface InstitutionalRecord {
  date: string;
  dealer_self?: InstitutionalItem;
  dealer_hedge?: InstitutionalItem;
  investment_trust?: InstitutionalItem;
  foreign_investor?: InstitutionalItem;
  foreign_dealer?: InstitutionalItem;
  total?: InstitutionalItem;
  // 上櫃額外欄位
  foreign_total?: InstitutionalItem;
  dealer_total?: InstitutionalItem;
}

export interface MarginItem {
  buy: number;
  sell: number;
  cash_repay: number;
  prev_balance: number;
  today_balance: number;
}

export interface MarginRecord {
  date: string;
  margin_buy?: MarginItem;
  short_sell?: MarginItem;
  margin_buy_amount?: MarginItem;
}

export interface FuturesOIRecord {
  date: string;
  total_volume: number;
  total_oi: number;
  front_month_close: number;
  front_month_oi: number;
}

export interface FuturesInstitutionalItem {
  name: string;
  long_deal_volume: number;
  short_deal_volume: number;
  long_oi_volume: number;
  short_oi_volume: number;
  net_oi_volume: number;
  long_oi_amount: number;
  short_oi_amount: number;
  net_oi_amount: number;
}

export interface FuturesInstitutionalRecord {
  date: string;
  dealer?: FuturesInstitutionalItem;
  investment_trust?: FuturesInstitutionalItem;
  foreign_investor?: FuturesInstitutionalItem;
}

export function useMarketApi() {
  const config = useRuntimeConfig();
  const baseUrl = config.public.apiBase;

  const fetchInstitutional = async (
    market: "twse" | "tpex",
    days: number = 30
  ): Promise<InstitutionalRecord[]> => {
    const res = await $fetch<{ success: boolean; data: InstitutionalRecord[] }>(
      `${baseUrl}/market/institutional/${market}`,
      { params: { days } }
    );
    return res.data;
  };

  const fetchMargin = async (days: number = 30): Promise<MarginRecord[]> => {
    const res = await $fetch<{ success: boolean; data: MarginRecord[] }>(
      `${baseUrl}/market/margin`,
      { params: { days } }
    );
    return res.data;
  };

  const fetchFuturesOI = async (days: number = 30): Promise<FuturesOIRecord[]> => {
    const res = await $fetch<{ success: boolean; data: FuturesOIRecord[] }>(
      `${baseUrl}/market/futures-oi`,
      { params: { days } }
    );
    return res.data;
  };

  const fetchFuturesInstitutional = async (days: number = 30): Promise<FuturesInstitutionalRecord[]> => {
    const res = await $fetch<{ success: boolean; data: FuturesInstitutionalRecord[] }>(
      `${baseUrl}/market/futures-institutional`,
      { params: { days } }
    );
    return res.data;
  };

  return { fetchInstitutional, fetchMargin, fetchFuturesOI, fetchFuturesInstitutional };
}
