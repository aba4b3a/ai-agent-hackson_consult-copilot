# Project Cost Guard Overlay（プロジェクト用コスト上書き）

`.ai-common/standards/COST_GUARD.base.md` の **後ろに** 適用されます。プロジェクトの予算上限と承認者を上書きします。

## 予算

- 月次上限（USD）:  <!-- base 既定値: 300 -->
- アラート閾値: 50%, 80%, 100%
- ハードストップ: プロジェクト判断（**人間が止める**。エージェントは自動停止しない）

## サービス上限

- Cloud Run `back/`:   min=0  max=
- Cloud Run `agent/`:  min=0  max=
- Cloud Build: 月次の build 分数上限 =
- Cloud Storage: 月次の TB-month 上限 =
- Firestore: 月次の read / write 上限 =
- BigQuery: 利用する? <!-- 既定: 利用しない -->
- AI 呼び出し: PR あたりトークン上限 =;  日次トークン上限 =

## プロジェクト固有の高コスト懸念

- <!-- 例: 「アップロード画像 1 枚ごとに OCR を走らせる。ユーザあたり 1 日 N 件まで」 -->

## 承認者

- コスト waiver 承認者:
- 高コストモデル利用承認者:
