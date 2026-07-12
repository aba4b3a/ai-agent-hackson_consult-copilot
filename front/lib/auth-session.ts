export type CompanyOption = {
  code: string;
  name: string;
  segment: string;
};

export type AuthSession = {
  consultantName: string;
  email: string;
  companyCode: string;
};

export const consultantCompanies: CompanyOption[] = [
  { code: "SMB-1042", name: "北斗精密工業", segment: "製造業 / 現場ナレッジ形成" },
  { code: "SMB-2198", name: "青葉ベーカリー&カフェ", segment: "飲食・小売 / 客単価と廃棄率改善" },
  { code: "SMB-3307", name: "みなとケア", segment: "介護サービス / 稼働率管理" },
  { code: "SMB-4811", name: "東都リフォーム", segment: "住宅施工 / 粗利管理" },
];

export const authSessionStorageKey = "knowledge-farmer.auth-session";
