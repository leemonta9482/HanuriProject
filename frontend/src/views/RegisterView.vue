<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import { fetchPublicSchools, checkUserIdAvailable, registerUser, verifyStudentId, sendRegistrationEmailCode, verifyRegistrationEmailCode } from '@/api/auth'
import type { PublicSchoolItem } from '@/api/types'

const router = useRouter()

const userId = ref('')
const password = ref('')
const passwordConfirm = ref('')
const name = ref('')
const schoolName = ref('')
const phone = ref('')
const email = ref('')
const studentId = ref('')
const interestMajor = ref('')
const studentIdCard = ref<File | null>(null)

const error = ref('')
const loading = ref(false)
const verificationToken = ref<string | null>(null)
const verifyError = ref('')
const verifyOk = ref(false)
const verifyLoading = ref(false)

const schools = ref<PublicSchoolItem[]>([])
const schoolsLoading = ref(false)
const schoolsError = ref('')

const userIdVerifiedFor = ref<string | null>(null)
const userIdCheckError = ref('')
const userIdCheckLoading = ref(false)

const emailCode = ref('')
const emailChallengeToken = ref<string | null>(null)
const emailCodeRequestFor = ref<string | null>(null)
const emailVerificationToken = ref<string | null>(null)
const emailVerifiedFor = ref<string | null>(null)
const emailSendError = ref('')
const emailVerifyError = ref('')
const emailSendHint = ref('')
const emailSendLoading = ref(false)
const emailVerifyLoading = ref(false)

type AgreementKey = 'age' | 'tos' | 'privacy' | 'community' | 'marketing'

interface AgreementDoc {
  key: AgreementKey
  label: string
  required: boolean
  /** 모달 본문. 비어 있으면 상세 보기(›) 버튼이 표시되지 않습니다. */
  body?: string
  /** 좌측 [필수]/[선택] 태그 표시 여부 (기본 true) */
  showTag?: boolean
}

const AGREEMENTS: readonly AgreementDoc[] = [
  {
    key: 'age',
    label: '만 14세 이상입니다.',
    required: true,
    showTag: false,
  },
  {
    key: 'tos',
    label: '이용약관 동의',
    required: true,
    body: `제1조 (목적)
이 약관은 “하누리”(이하 “서비스”)를 운영하는 운영주체(이하 “운영팀”)가 제공하는 캠퍼스(학교) 단위 중고거래 및 관련 부가 서비스의 이용 조건과 절차, 운영팀과 회원의 권리·의무·책임 사항을 규정함을 목적으로 합니다.

제2조 (용어의 정의)
1. “회원”이란 본 약관 및 개인정보처리방침에 동의하고 학생증 인증을 거쳐 가입 신청을 완료한 사람을 말합니다.
2. “게시물”이란 회원이 서비스에 등록한 판매글, 구매 희망글, 사진, 채팅 메시지, 신고 내용 등 모든 정보를 말합니다.
3. “학교 피드”란 회원이 등록한 학교명을 기준으로, 같은 학교 회원의 게시물만 보이도록 제공되는 목록을 말합니다.

제3조 (약관의 효력과 개정)
1. 본 약관은 서비스 화면에 게시함으로써 효력이 발생합니다.
2. 운영팀은 관계 법령을 위반하지 않는 범위에서 약관을 개정할 수 있으며, 개정 시 시행일 7일 전(회원에게 불리하거나 중대한 변경은 30일 전)부터 공지합니다.

제4조 (회원가입과 학생 인증)
1. 회원가입은 운영팀이 등록·노출한 학교(School) 중에서 본인 소속 학교를 선택한 뒤, 학생증 이미지 업로드와 OCR 기반 자동 검증(이름·학교명·학번 일치)을 통과해야 신청이 접수됩니다.
2. 가입 신청은 운영팀의 승인 절차를 거친 뒤에 로그인할 수 있으며, 운영팀은 다음 각 호에 해당하는 경우 가입을 승인하지 않거나 사후에 자격을 박탈할 수 있습니다.
   - 학생증 정보가 명확하지 않거나 위·변조가 의심되는 경우
   - 본인이 아닌 타인의 정보로 가입 신청한 경우
   - 같은 학교·동일 학번으로 이미 가입된 계정이 있는 경우
   - 이메일 인증을 완료하지 않은 경우
   - 그 밖에 본 약관, 개인정보처리방침, 운영정책을 위반한 경우

제5조 (서비스의 내용)
1. 서비스는 같은 학교 회원 간의 중고 물품 직거래·구매 희망 등록, 1:1 채팅, 찜, 신고, 알림 등을 제공합니다.
2. 운영팀은 거래의 당사자가 아니며, 회원 간 거래에서 발생하는 분쟁·결제·물품 인도 등에 대해 책임을 지지 않습니다. 운영팀은 신고 접수 등 운영상 필요한 범위에서 게시물 비공개·삭제, 계정 사용 제한 등의 조치만을 수행합니다.

제6조 (계정 관리)
1. 회원은 아이디·비밀번호를 직접 관리하며, 제3자에게 양도하거나 공유할 수 없습니다.
2. 동일 계정에 새 로그인이 발생하면 이전 세션 토큰은 자동으로 무효화됩니다.
3. 회원은 언제든지 탈퇴를 요청할 수 있으며, 탈퇴 시 본 약관·개인정보처리방침에 따라 회원 정보가 처리됩니다.

제7조 (게시물에 대한 권리와 책임)
1. 게시물의 저작권은 작성자에게 있으나, 운영팀은 서비스 운영·노출·캐싱·백업 목적의 범위에서 해당 게시물을 사용할 수 있습니다.
2. 회원은 자신이 작성한 게시물의 적법성과 정확성에 대해 책임을 지며, 타인의 권리(저작권·초상권·개인정보 등)를 침해하는 게시물을 등록할 수 없습니다.

제8조 (서비스 이용 제한)
운영팀은 회원이 본 약관, 개인정보처리방침, 운영정책을 위반한 경우 게시물 삭제, 채팅 차단, 일정 기간 이용 제한 또는 계정 삭제 등의 조치를 취할 수 있습니다.

제9조 (면책)
운영팀은 천재지변, 통신 장애, 기타 운영팀의 합리적 통제 범위를 벗어난 사유로 인한 서비스 중단·지연·데이터 손실에 대해 책임을 지지 않습니다.

부칙
본 약관은 게시일부터 시행됩니다.`,
  },
  {
    key: 'privacy',
    label: '개인정보처리방침 동의',
    required: true,
    body: `“하누리”(이하 “서비스”) 운영팀은 「개인정보 보호법」 등 관련 법령을 준수하며, 회원의 개인정보를 다음과 같이 수집·이용합니다.

1. 수집하는 개인정보 항목
[필수]
- 이름, 학교명, 학번
- 학생증 이미지 파일(가입 신청 시 업로드)
- 아이디(로그인 식별자), 비밀번호(서버에는 bcrypt 해시로만 저장)
- 휴대전화번호, 이메일
[선택]
- 관심 전공, 프로필 사진
[서비스 이용 과정에서 자동 생성·수집되는 정보]
- 매너 온도, 신뢰 점수, 계정 상태(활성/휴면/삭제), 가입 승인 상태(대기/승인/거절)
- 회원이 작성한 판매글·구매 희망글·이미지, 찜 내역, 채팅방·채팅 메시지, 차단 목록, 신고 내역, 인앱 알림
- 로그인용 토큰 버전 정보(이전 세션 무효화 목적)
- 접속 IP·기기·브라우저 정보(서버 로그)

2. 수집·이용 목적
- 회원 식별 및 본인 확인(학생증 OCR 자동 검증, 같은 학교·학번 중복 가입 차단)
- 가입 승인·계정 관리, 부정 이용·도용 방지
- 같은 학교 회원에게 한정된 게시물·피드·채팅·찜·알림 제공
- 거래 관련 분쟁 조사, 신고 처리, 운영·고객 응대
- 서비스 공지, 가입 거절 등 운영상 필수 안내 메일 발송
- 서비스 품질 개선, 통계·분석(개인을 식별할 수 없는 형태)

3. 보유·이용 기간 및 파기
- 원칙: 회원 탈퇴 또는 계정 삭제 시 지체 없이 파기합니다. 학생증 이미지·프로필 사진 등 업로드 파일은 회원 행 삭제와 함께 서버에서 제거됩니다.
- 가입 거절: 운영자가 가입을 거절한 경우, 거절 안내 메일 발송이 정상 완료된 시점에 회원 정보(학생증 이미지 포함)는 즉시 삭제됩니다.
- 다만 관계 법령(전자상거래법, 통신비밀보호법 등)에 따라 일정 기간 보관 의무가 있는 정보는 해당 기간 동안 다른 정보와 분리해 보관 후 파기합니다.

4. 제3자 제공
운영팀은 회원의 개인정보를 외부에 제공하지 않습니다. 다만 법령에 근거하거나 수사기관의 적법한 요청이 있는 경우는 예외로 합니다.

5. 처리 위탁
- 메일 발송: 가입 거절·운영 알림 메일은 운영팀이 설정한 SMTP 서비스(예: Gmail SMTP 등)를 통해 발송될 수 있습니다.
- 호스팅·DB·파일 저장은 운영팀이 사용 중인 인프라 환경에서 처리됩니다. 위탁 업체가 변경될 경우 본 방침을 갱신하여 공지합니다.

6. 회원의 권리와 행사 방법
회원은 언제든지 본인의 개인정보를 조회·수정할 수 있으며, 탈퇴(처리 정지·삭제)를 요청할 수 있습니다. 또한 운영팀에 처리 현황 확인을 요청할 수 있습니다.

7. 안전성 확보 조치
- 비밀번호는 평문 저장 없이 bcrypt 해시로만 보관합니다.
- 로그인 시마다 토큰 버전을 갱신해 이전 세션 토큰을 무효화합니다.
- 학생증 이미지 등 업로드 파일은 권한이 있는 사용자(본인·관리자)만 접근 가능한 경로로 관리합니다.

8. 만 14세 미만 아동의 회원가입 제한
본 서비스는 대학생 등 만 14세 이상을 대상으로 합니다. 만 14세 미만은 가입할 수 없습니다.

9. 개인정보 보호 책임 안내
개인정보 관련 문의·열람·정정·삭제 요청은 서비스 내 문의 채널 또는 운영팀이 안내한 연락처로 접수해 주세요.`,
  },
  {
    key: 'community',
    label: '운영정책(커뮤니티 규칙) 동의',
    required: true,
    body: `“하누리”는 같은 학교 회원 간의 안전한 중고거래를 위한 서비스입니다. 모든 회원은 다음 운영정책을 준수해야 합니다.

1. 게시물 작성 규칙
- 판매글·구매 희망글의 제목·가격·설명·이미지는 사실에 근거해 정확하게 작성합니다.
- 같은 글의 반복 등록(도배), 무관한 광고·홍보, 외부 사이트로의 유도는 금지됩니다.
- 거래와 무관한 정치·종교적 선전, 차별·혐오 표현은 작성할 수 없습니다.

2. 거래 금지 품목
- 「청소년 보호법」상 청소년 유해 매체물, 음란물
- 주류·담배·전자담배 등 연령 제한 상품
- 마약류·향정신성의약품, 처방 의약품
- 무기·총포·도검·화약류, 위험물
- 위·변조 상품, 도난품, 타인 명의의 학생증·신분증·계정·증명서
- 보이스피싱·대포통장·작업 대출 등 불법 금융 거래
- 그 밖에 법령상 거래가 금지된 모든 물품·서비스

3. 채팅·소통 규칙
- 욕설·모욕·성희롱·협박·스토킹·차별 발언을 금지합니다.
- 거래 목적 외의 사적 연락처 강요, 불필요한 신상 정보 요구를 금지합니다.
- 채팅 내 사기·허위 결제 유도(가짜 송금 화면, 가짜 안전결제 링크 등)는 즉시 신고 대상이며 제재 사유입니다.

4. 신원 도용·계정 부정 사용 금지
- 타인의 학생증·신분증·이름·학번으로 가입할 수 없으며, 자신의 계정을 타인에게 양도·공유하는 행위도 금지됩니다.
- 운영팀은 학생증 OCR 검증과 같은 학교·동일 학번 중복 가입 차단을 적용합니다.

5. 신고·차단 기능
- 부적절한 게시물이나 사용자는 신고 기능으로 알려 주세요. 운영팀은 접수된 신고를 검토하여 조치합니다.
- 회원은 특정 사용자를 차단해 해당 사용자의 채팅·접근을 제한할 수 있습니다.

6. 운영팀의 조치
운영팀은 본 운영정책, 이용약관, 개인정보처리방침 위반이 확인되거나 의심되는 경우 다음 중 하나 이상의 조치를 취할 수 있습니다.
- 게시물 비공개 또는 삭제
- 채팅방 종료, 메시지 전송 제한
- 일정 기간 서비스 이용 제한
- 가입 거절 또는 계정 삭제
- 수사기관 신고 등 법적 조치

7. 분쟁 처리
운영팀은 회원 간 거래의 당사자가 아니므로, 거래 과정에서 발생한 손해·물품 하자·결제 분쟁에 대해 책임을 지지 않습니다. 다만 신고 접수와 운영상 필요한 범위에서 사실 확인과 중재 절차를 지원할 수 있습니다.`,
  },
  {
    key: 'marketing',
    label: '마케팅 수신 동의',
    required: false,
    body: `본 동의는 선택 사항이며, 동의하지 않아도 회원가입 및 “하누리”의 기본 기능 이용에는 제한이 없습니다.

1. 수집·이용 목적
- 신규 기능·이벤트·캠퍼스 단위 프로모션 안내
- 회원의 관심 전공·학교를 고려한 추천 콘텐츠(인기 판매글·구매 희망글 등) 안내
- 서비스 이용 활성화를 위한 안내성 정보 제공

2. 발송 채널 및 수단
- 이메일(가입 시 등록한 주소)
- 향후 인앱 알림 기능 확장 시, 동의한 회원에 한해 마케팅 성격의 인앱 알림이 함께 발송될 수 있습니다.
※ 거래 알림(채팅 수신·찜 알림 등) 및 가입 승인·거절 등 운영 필수 알림은 본 동의 여부와 관계없이 항상 발송됩니다.

3. 보유·이용 기간
회원 탈퇴 또는 본 동의 철회 시까지 보관·이용합니다.

4. 동의 철회 방법
- 마이페이지에서 마케팅 수신 설정을 변경(추후 제공)
- 발송된 이메일 하단의 수신 거부(unsubscribe) 링크 이용
- 운영팀에 직접 철회 요청

5. 안내 사항
정보통신망법에 따라 광고성 정보를 야간(21시~익일 8시)에 전자적 전송 매체로 발송할 경우, 별도의 야간 수신 동의를 추가로 받습니다. 본 동의는 야간 수신 동의를 포함하지 않습니다.`,
  },
] as const

const agreementChecked = ref<Record<AgreementKey, boolean>>({
  age: false,
  tos: false,
  privacy: false,
  community: false,
  marketing: false,
})

const requiredAgreementKeys: AgreementKey[] = AGREEMENTS.filter((a) => a.required).map((a) => a.key)

const requiredAgreementsOk = computed(() =>
  requiredAgreementKeys.every((k) => agreementChecked.value[k]),
)

const allAgreed = computed(() => AGREEMENTS.every((a) => agreementChecked.value[a.key]))

function toggleAllAgreements() {
  const next = !allAgreed.value
  for (const a of AGREEMENTS) {
    agreementChecked.value[a.key] = next
  }
}

const agreementModalKey = ref<AgreementKey | null>(null)
const activeAgreement = computed<AgreementDoc | null>(() => {
  const k = agreementModalKey.value
  if (!k) return null
  return AGREEMENTS.find((a) => a.key === k) ?? null
})

function openAgreement(key: AgreementKey) {
  agreementModalKey.value = key
}

function closeAgreement() {
  agreementModalKey.value = null
}

const userIdLocked = computed(
  () => !!userIdVerifiedFor.value && userId.value.trim() === userIdVerifiedFor.value,
)

const emailLocked = computed(
  () =>
    !!emailVerifiedFor.value && email.value.trim().toLowerCase() === emailVerifiedFor.value,
)

function clearEmailVerification() {
  emailChallengeToken.value = null
  emailCodeRequestFor.value = null
  emailVerificationToken.value = null
  emailVerifiedFor.value = null
  emailCode.value = ''
  emailSendError.value = ''
  emailVerifyError.value = ''
  emailSendHint.value = ''
}

function onEmailInput() {
  const t = email.value.trim().toLowerCase()
  if (emailVerifiedFor.value !== null && t !== emailVerifiedFor.value) {
    clearEmailVerification()
    return
  }
  if (emailCodeRequestFor.value !== null && t !== emailCodeRequestFor.value) {
    emailChallengeToken.value = null
    emailCodeRequestFor.value = null
    emailCode.value = ''
    emailSendError.value = ''
    emailVerifyError.value = ''
    emailSendHint.value = ''
    emailVerificationToken.value = null
    emailVerifiedFor.value = null
  }
}

function onEmailCodeInput() {
  const d = emailCode.value.replace(/\D/g, '').slice(0, 4)
  if (d !== emailCode.value) emailCode.value = d
}

function unlockEmail() {
  clearEmailVerification()
}

async function onSendEmailCode() {
  emailSendError.value = ''
  emailVerifyError.value = ''
  emailSendHint.value = ''
  const addr = email.value.trim()
  if (!addr) {
    emailSendError.value = '이메일을 입력해 주세요.'
    return
  }
  emailSendLoading.value = true
  try {
    const res = await sendRegistrationEmailCode(addr)
    emailChallengeToken.value = res.challenge_token
    emailCodeRequestFor.value = addr.toLowerCase()
    emailVerificationToken.value = null
    emailVerifiedFor.value = null
    emailCode.value = ''
    emailSendHint.value = '인증번호가 메일로 발송되었습니다. 스팸함도 확인해 주세요.'
  } catch (e) {
    emailSendError.value = e instanceof Error ? e.message : '인증번호 발송에 실패했습니다.'
  } finally {
    emailSendLoading.value = false
  }
}

async function onVerifyEmailCode() {
  emailVerifyError.value = ''
  if (!emailChallengeToken.value) {
    emailVerifyError.value = '먼저 인증번호 받기를 눌러 주세요.'
    return
  }
  const digits = emailCode.value.replace(/\D/g, '')
  if (digits.length !== 4) {
    emailVerifyError.value = '인증번호 4자리를 입력해 주세요.'
    return
  }
  emailVerifyLoading.value = true
  try {
    const res = await verifyRegistrationEmailCode(emailChallengeToken.value, digits)
    emailVerificationToken.value = res.email_verification_token
    emailVerifiedFor.value = email.value.trim().toLowerCase()
    emailSendHint.value = ''
  } catch (e) {
    emailVerifyError.value = e instanceof Error ? e.message : '인증에 실패했습니다.'
  } finally {
    emailVerifyLoading.value = false
  }
}

function unlockUserId() {
  userIdVerifiedFor.value = null
  userIdCheckError.value = ''
}

async function loadSchools() {
  schoolsError.value = ''
  schoolsLoading.value = true
  try {
    const res = await fetchPublicSchools()
    schools.value = res.items
  } catch (e) {
    schoolsError.value = e instanceof Error ? e.message : '학교 목록을 불러오지 못했습니다.'
    schools.value = []
  } finally {
    schoolsLoading.value = false
  }
}

onMounted(() => loadSchools())

function onStudentCardChange(ev: Event) {
  const input = ev.target as HTMLInputElement
  const file = input.files?.[0]
  studentIdCard.value = file ?? null
  verificationToken.value = null
  verifyOk.value = false
  verifyError.value = ''
}

function onUserIdInput() {
  const t = userId.value.trim()
  if (userIdVerifiedFor.value !== null && t !== userIdVerifiedFor.value) {
    userIdVerifiedFor.value = null
  }
  userIdCheckError.value = ''
}

async function onCheckUserId() {
  userIdCheckError.value = ''
  const id = userId.value.trim()
  if (!id) {
    userIdCheckError.value = '아이디를 입력해 주세요.'
    userIdVerifiedFor.value = null
    return
  }
  userIdCheckLoading.value = true
  try {
    const res = await checkUserIdAvailable(id)
    if (res.available) {
      userIdVerifiedFor.value = id
      userIdCheckError.value = ''
    } else {
      userIdVerifiedFor.value = null
      userIdCheckError.value = '이미 사용 중인 아이디입니다.'
    }
  } catch (e) {
    userIdVerifiedFor.value = null
    userIdCheckError.value = e instanceof Error ? e.message : '중복 확인에 실패했습니다.'
  } finally {
    userIdCheckLoading.value = false
  }
}

function clearVerificationIfIdentityChanged() {
  verificationToken.value = null
  verifyOk.value = false
  verifyError.value = ''
}

async function onVerifyStudentId() {
  verifyError.value = ''
  verifyOk.value = false
  verificationToken.value = null
  const n = name.value.trim()
  const sn = schoolName.value.trim()
  const sid = studentId.value.trim()
  if (!n || !sn) {
    verifyError.value = '이름과 학교명을 입력한 뒤 인증해 주세요.'
    return
  }
  if (!sid) {
    verifyError.value = '학번을 입력한 뒤 인증해 주세요.'
    return
  }
  if (!studentIdCard.value) {
    verifyError.value = '학생증 이미지를 선택해 주세요.'
    return
  }
  verifyLoading.value = true
  try {
    const res = await verifyStudentId({
      name: n,
      school_name: sn,
      student_id: sid,
      student_id_card: studentIdCard.value,
    })
    verificationToken.value = res.verification_token
    verifyOk.value = true
  } catch (e) {
    verifyError.value = e instanceof Error ? e.message : '학생증 인증에 실패했습니다.'
  } finally {
    verifyLoading.value = false
  }
}

async function onSubmit() {
  error.value = ''
  if (password.value !== passwordConfirm.value) {
    error.value = '비밀번호가 일치하지 않습니다.'
    return
  }
  if (password.value.length < 8) {
    error.value = '비밀번호는 8자 이상이어야 합니다.'
    return
  }
  if (!studentIdCard.value) {
    error.value = '학생증 이미지를 첨부해 주세요.'
    return
  }
  if (!studentId.value.trim()) {
    error.value = '학번을 입력해 주세요.'
    return
  }
  if (!verificationToken.value) {
    error.value = '학생증 인증하기를 눌러 이름·학교명·학번이 카드와 일치하는지 확인해 주세요.'
    return
  }
  const uid = userId.value.trim()
  if (!userIdVerifiedFor.value || uid !== userIdVerifiedFor.value) {
    error.value = '아이디 중복 확인을 완료해 주세요.'
    return
  }
  if (
    !emailVerificationToken.value ||
    !emailVerifiedFor.value ||
    email.value.trim().toLowerCase() !== emailVerifiedFor.value
  ) {
    error.value = '이메일 인증을 완료해 주세요.'
    return
  }
  if (!requiredAgreementsOk.value) {
    error.value = '필수 약관에 모두 동의해 주세요.'
    return
  }
  loading.value = true
  try {
    await registerUser({
      user_id: userId.value.trim(),
      password: password.value,
      name: name.value.trim(),
      school_name: schoolName.value.trim(),
      phone: phone.value.trim(),
      email: email.value.trim(),
      student_id: studentId.value.trim(),
      interest_major: interestMajor.value.trim() || null,
      student_id_card: studentIdCard.value,
      student_id_verification_token: verificationToken.value,
      email_verification_token: emailVerificationToken.value,
    })
    await router.push({ name: 'login', query: { pending: '1' } })
  } catch (e) {
    error.value = e instanceof Error ? e.message : '회원가입에 실패했습니다.'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="auth-page">
    <div class="card">
      <h1 class="title">회원가입</h1>
      <p class="lead">
        가입 신청 후 관리자 승인이 완료되어야<br>
        로그인할 수 있습니다.
      </p>
      <form class="form" @submit.prevent="onSubmit">
        <label class="field">
          <span class="label">이름 <span class="req">*</span></span>
          <input
            v-model="name"
            type="text"
            name="name"
            required
            maxlength="50"
            placeholder="학생증과 동일하게"
            @input="clearVerificationIfIdentityChanged"
          />
        </label>
        <label class="field">
          <span class="label">학교명 <span class="req">*</span></span>
          <select
            v-model="schoolName"
            name="school_name"
            required
            class="field-select"
            :disabled="schoolsLoading || !!schoolsError"
            @change="clearVerificationIfIdentityChanged"
          >
            <option value="" disabled>
              {{ schoolsLoading ? '학교 목록 불러오는 중…' : '학교를 선택해 주세요' }}
            </option>
            <option v-for="s in schools" :key="s.school_id" :value="s.name">
              {{ s.name }}{{ s.region ? ` (${s.region})` : '' }}
            </option>
          </select>
          <span v-if="schoolsError" class="file-hint" style="color: #c0392b">{{ schoolsError }}</span>
          <span v-else-if="!schoolsLoading && !schools.length" class="file-hint">
            등록된 학교가 없습니다. 관리자에게 문의해 주세요.
          </span>
        </label>
        <label class="field">
          <span class="label">학번 <span class="req">*</span></span>
          <input
            v-model="studentId"
            type="text"
            name="student_id"
            required
            maxlength="20"
            placeholder="학생증에 적힌 학번 그대로"
            @input="clearVerificationIfIdentityChanged"
          />
        </label>
        <label class="field">
          <span class="label">학생증 이미지 <span class="req">*</span></span>
          <input
            type="file"
            name="student_id_card"
            accept="image/jpeg,image/png,image/webp,image/gif"
            required
            class="file-input"
            @change="onStudentCardChange"
          />
          <span class="file-hint">JPEG, PNG, WebP, GIF · 최대 5MB</span>
        </label>
        <div class="verify-row">
          <button
            type="button"
            class="btn-verify"
            :disabled="verifyLoading || loading"
            @click="onVerifyStudentId"
          >
            {{ verifyLoading ? '인증 중…' : '학생증 인증하기' }}
          </button>
        </div>
        <p v-if="verifyOk" class="hint success" role="status">학생증과 이름·학교명·학번이 일치합니다. 아래 정보를 입력한 뒤 가입해 주세요.</p>
        <p v-if="verifyError" class="hint error" role="alert">{{ verifyError }}</p>

        <label class="field">
          <span class="label">아이디 <span class="req">*</span></span>
          <div class="user-id-row">
            <input
              v-model="userId"
              type="text"
              name="user_id"
              autocomplete="username"
              required
              maxlength="50"
              placeholder="로그인에 사용할 아이디"
              class="user-id-input"
              :readonly="userIdLocked"
              @input="onUserIdInput"
            />
            <button
              type="button"
              class="btn-id-check"
              :disabled="userIdCheckLoading || loading || userIdLocked"
              @click="onCheckUserId"
            >
              {{ userIdCheckLoading ? '확인 중…' : '중복 확인' }}
            </button>
          </div>
          <p v-if="userIdLocked" class="hint success user-id-success" role="status">
            사용 가능한 아이디입니다.
            <button type="button" class="btn-id-change" @click="unlockUserId">다른 아이디로 변경</button>
          </p>
          <p v-if="userIdCheckError" class="hint error" role="alert">{{ userIdCheckError }}</p>
        </label>

        <label class="field">
          <span class="label">비밀번호 <span class="req">*</span></span>
          <input
            v-model="password"
            type="password"
            name="password"
            autocomplete="new-password"
            required
            minlength="8"
            maxlength="128"
            placeholder="8자 이상"
          />
        </label>
        <label class="field">
          <span class="label">비밀번호 확인 <span class="req">*</span></span>
          <input
            v-model="passwordConfirm"
            type="password"
            name="password_confirm"
            autocomplete="new-password"
            required
            placeholder="비밀번호 다시 입력"
          />
        </label>
        <label class="field">
          <span class="label">전화번호 <span class="req">*</span></span>
          <input
            v-model="phone"
            type="tel"
            name="phone"
            required
            maxlength="20"
            placeholder="010-0000-0000"
          />
        </label>
        <label class="field">
          <span class="label">이메일 <span class="req">*</span></span>
          <input
            v-model="email"
            type="email"
            name="email"
            required
            placeholder="email@example.com"
            autocomplete="email"
            class="email-text-input"
            :readonly="emailLocked"
            @input="onEmailInput"
          />
          <div class="email-send-row">
            <button
              type="button"
              class="btn-email-send"
              :disabled="emailSendLoading || loading || emailLocked"
              @click="onSendEmailCode"
            >
              {{ emailSendLoading ? '발송 중…' : '인증번호 받기' }}
            </button>
          </div>
          <p v-if="emailSendHint" class="hint email-hint-ok">{{ emailSendHint }}</p>
          <p v-if="emailSendError" class="hint error" role="alert">{{ emailSendError }}</p>
          <div class="email-code-row">
            <input
              v-model="emailCode"
              type="text"
              name="email_code"
              inputmode="numeric"
              maxlength="4"
              autocomplete="one-time-code"
              placeholder="인증번호 4자리"
              class="email-code-input"
              :disabled="!emailChallengeToken || emailLocked"
              @input="onEmailCodeInput"
            />
            <button
              type="button"
              class="btn-email-verify"
              :disabled="emailVerifyLoading || loading || emailLocked || !emailChallengeToken"
              @click="onVerifyEmailCode"
            >
              {{ emailVerifyLoading ? '확인 중…' : '인증 확인' }}
            </button>
          </div>
          <p v-if="emailLocked" class="hint success user-id-success" role="status">
            이메일 인증이 완료되었습니다.
            <button type="button" class="btn-id-change" @click="unlockEmail">이메일 변경</button>
          </p>
          <p v-if="emailVerifyError" class="hint error" role="alert">{{ emailVerifyError }}</p>
        </label>
        <label class="field">
          <span class="label">관심 전공</span>
          <input
            v-model="interestMajor"
            type="text"
            name="interest_major"
            maxlength="100"
            placeholder="선택"
          />
        </label>
        <section class="agreements" aria-label="약관 동의">
          <label class="agree agree--master">
            <input
              type="checkbox"
              :checked="allAgreed"
              @change="toggleAllAgreements"
            />
            <span class="agree-label agree-label--master">모두 동의합니다.</span>
          </label>
          <div class="agree-divider" aria-hidden="true" />
          <ul class="agree-list">
            <li v-for="a in AGREEMENTS" :key="a.key" class="agree-item">
              <label class="agree">
                <input
                  type="checkbox"
                  v-model="agreementChecked[a.key]"
                />
                <span class="agree-label">
                  <span
                    v-if="a.showTag !== false"
                    :class="['agree-tag', a.required ? 'agree-tag--req' : 'agree-tag--opt']"
                  >
                    [{{ a.required ? '필수' : '선택' }}]
                  </span>
                  {{ a.label }}
                </span>
              </label>
              <button
                v-if="a.body"
                type="button"
                class="agree-detail"
                :aria-label="`${a.label} 자세히 보기`"
                @click="openAgreement(a.key)"
              >
                <span aria-hidden="true">›</span>
              </button>
            </li>
          </ul>
        </section>

        <p v-if="error" class="hint error" role="alert">{{ error }}</p>
        <button
          class="submit"
          type="submit"
          :disabled="
            loading ||
            !verificationToken ||
            !userIdVerifiedFor ||
            userId.trim() !== userIdVerifiedFor ||
            !emailVerificationToken ||
            !emailVerifiedFor ||
            email.trim().toLowerCase() !== emailVerifiedFor ||
            !requiredAgreementsOk
          "
        >
          {{ loading ? '처리 중…' : '가입 신청하기' }}
        </button>
      </form>

      <div
        v-if="activeAgreement"
        class="modal-backdrop"
        role="presentation"
        @click.self="closeAgreement"
      >
        <div
          class="modal"
          role="dialog"
          aria-modal="true"
          :aria-label="activeAgreement.label"
        >
          <header class="modal-head">
            <h2 class="modal-title">
              {{ activeAgreement.label }}
              <span :class="['agree-tag', activeAgreement.required ? 'agree-tag--req' : 'agree-tag--opt']">
                ({{ activeAgreement.required ? '필수' : '선택' }})
              </span>
            </h2>
            <button
              type="button"
              class="modal-close"
              aria-label="닫기"
              @click="closeAgreement"
            >
              <span aria-hidden="true">×</span>
            </button>
          </header>
          <div class="modal-body">
            <pre class="modal-text">{{ activeAgreement.body }}</pre>
          </div>
          <footer class="modal-foot">
            <button type="button" class="btn-modal-confirm" @click="closeAgreement">확인</button>
          </footer>
        </div>
      </div>
      <p class="footer">
        이미 계정이 있으신가요?
        <RouterLink class="link" to="/login">로그인</RouterLink>
      </p>
    </div>
  </div>
</template>

<style scoped>
.auth-page {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem 0;
  min-height: min(80vh, 900px);
}

.card {
  width: 100%;
  max-width: 440px;
  padding: 2rem;
  border-radius: 12px;
  background: var(--color-background-soft);
  border: 1px solid var(--color-border);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.06);
}

.title {
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--color-heading);
  margin-bottom: 0.75rem;
  text-align: center;
}

.lead {
  font-size: 0.875rem;
  line-height: 1.5;
  color: var(--color-text);
  opacity: 0.9;
  margin-bottom: 1.25rem;
  text-align: center;
}

.form {
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.label {
  font-size: 0.875rem;
  color: var(--color-text);
}

.req {
  color: hsl(186, 38%, 32%);
}

.field input {
  padding: 0.65rem 0.75rem;
  border-radius: 8px;
  border: 1px solid var(--color-border);
  background: var(--color-background);
  color: var(--color-text);
  font-size: 1rem;
}

.field input:focus {
  outline: 2px solid rgba(92, 176, 185, 0.45);
  outline-offset: 0;
  border-color: rgba(92, 176, 185, 0.6);
}

.user-id-row {
  display: flex;
  gap: 0.5rem;
  align-items: stretch;
}

.user-id-row .user-id-input {
  flex: 1;
  min-width: 0;
}

.user-id-input:read-only {
  background: rgba(0, 0, 0, 0.04);
  cursor: default;
  color: var(--color-text);
}

.field .email-text-input:read-only {
  background: rgba(0, 0, 0, 0.04);
  cursor: default;
  color: var(--color-text);
}

.user-id-success {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.5rem 0.75rem;
}

.btn-id-change {
  margin: 0;
  padding: 0;
  border: none;
  background: none;
  color: hsl(186, 38%, 32%);
  font: inherit;
  font-size: 0.85rem;
  font-weight: 600;
  text-decoration: underline;
  text-underline-offset: 2px;
  cursor: pointer;
}

.btn-id-change:hover {
  color: hsl(186, 45%, 24%);
}

.btn-id-check {
  flex: 0 0 auto;
  padding: 0.65rem 0.9rem;
  border-radius: 8px;
  border: 1px solid var(--color-accent);
  background: rgba(92, 176, 185, 0.1);
  color: hsl(186, 38%, 28%);
  font-weight: 600;
  font-size: 0.85rem;
  white-space: nowrap;
  cursor: pointer;
  transition: background 0.15s;
}

.btn-id-check:hover:not(:disabled) {
  background: rgba(92, 176, 185, 0.18);
}

.btn-id-check:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.field-select {
  padding: 0.65rem 0.75rem;
  border-radius: 8px;
  border: 1px solid var(--color-border);
  background: var(--color-background);
  color: var(--color-text);
  font-size: 1rem;
  appearance: auto;
}

.field-select:focus {
  outline: 2px solid rgba(92, 176, 185, 0.45);
  outline-offset: 0;
  border-color: rgba(92, 176, 185, 0.6);
}

.field-select:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.file-input {
  padding: 0.5rem 0 !important;
  font-size: 0.9rem !important;
}

.file-hint {
  font-size: 0.75rem;
  opacity: 0.8;
}

.hint {
  font-size: 0.875rem;
  margin: 0;
}

.hint.error {
  color: #c0392b;
}

.hint.success {
  color: hsl(160, 45%, 28%);
  font-size: 0.82rem;
}

.verify-row {
  margin: -0.25rem 0 0.35rem;
}

.email-send-row {
  margin-top: 0.45rem;
}

.btn-email-send {
  width: 100%;
  padding: 0.55rem 1rem;
  border-radius: 8px;
  border: 1px solid var(--color-accent);
  background: transparent;
  color: hsl(186, 38%, 28%);
  font-weight: 600;
  font-size: 0.88rem;
  cursor: pointer;
  transition: background 0.15s;
}

.btn-email-send:hover:not(:disabled) {
  background: rgba(92, 176, 185, 0.12);
}

.btn-email-send:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.email-code-row {
  display: flex;
  gap: 0.5rem;
  align-items: stretch;
  margin-top: 0.55rem;
}

.email-code-input {
  flex: 1;
  min-width: 0;
  letter-spacing: 0.15em;
  font-variant-numeric: tabular-nums;
}

.btn-email-verify {
  flex: 0 0 auto;
  padding: 0.65rem 0.9rem;
  border-radius: 8px;
  border: 1px solid var(--color-accent);
  background: rgba(92, 176, 185, 0.1);
  color: hsl(186, 38%, 28%);
  font-weight: 600;
  font-size: 0.85rem;
  white-space: nowrap;
  cursor: pointer;
  transition: background 0.15s;
}

.btn-email-verify:hover:not(:disabled) {
  background: rgba(92, 176, 185, 0.18);
}

.btn-email-verify:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.email-hint-ok {
  margin-top: 0.35rem;
  font-size: 0.82rem;
  opacity: 0.9;
}

.btn-verify {
  width: 100%;
  padding: 0.65rem 1rem;
  border-radius: 8px;
  border: 1px solid var(--color-accent);
  background: transparent;
  color: hsl(186, 38%, 28%);
  font-weight: 600;
  font-size: 0.92rem;
  cursor: pointer;
  transition:
    background 0.15s,
    color 0.15s;
}

.btn-verify:hover:not(:disabled) {
  background: rgba(92, 176, 185, 0.12);
}

.btn-verify:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.submit {
  margin-top: 0.35rem;
  padding: 0.75rem 1rem;
  border: none;
  border-radius: 8px;
  background: var(--color-accent);
  color: #fff;
  font-weight: 600;
  font-size: 1rem;
  cursor: pointer;
  transition: filter 0.2s;
}

.submit:hover:not(:disabled) {
  filter: brightness(1.05);
}

.submit:disabled {
  opacity: 0.65;
  cursor: not-allowed;
}

.footer {
  margin-top: 1.5rem;
  text-align: center;
  font-size: 0.9rem;
  color: var(--color-text);
}

.link {
  font-weight: 600;
  margin-left: 0.25rem;
}

/* ---------- 약관 동의 ---------- */
.agreements {
  margin-top: 0.5rem;
  padding: 1rem 0.25rem 0.25rem;
}

.agree {
  display: flex;
  align-items: center;
  gap: 0.65rem;
  cursor: pointer;
  user-select: none;
}

.agree input[type='checkbox'] {
  flex: 0 0 auto;
  width: 18px;
  height: 18px;
  accent-color: hsl(186, 38%, 38%);
  cursor: pointer;
}

.agree-label {
  font-size: 0.95rem;
  color: var(--color-text);
  line-height: 1.4;
}

.agree-label--master {
  font-weight: 700;
  color: var(--color-heading);
  font-size: 1rem;
}

.agree-divider {
  height: 1px;
  background: var(--color-border);
  margin: 0.85rem 0 0.5rem;
}

.agree-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
}

.agree-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  padding: 0.4rem 0;
}

.agree-tag {
  font-weight: 600;
  margin-right: 0.2rem;
}

.agree-tag--req {
  color: hsl(186, 50%, 35%);
}

.agree-tag--opt {
  color: var(--color-text);
  opacity: 0.65;
}

.agree-detail {
  flex: 0 0 auto;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border: none;
  background: transparent;
  color: var(--color-text);
  opacity: 0.55;
  font-size: 1.45rem;
  line-height: 1;
  cursor: pointer;
  border-radius: 6px;
  transition: background 0.15s, opacity 0.15s;
}

.agree-detail:hover {
  background: rgba(0, 0, 0, 0.04);
  opacity: 1;
}

.agree-detail:focus-visible {
  outline: 2px solid rgba(92, 176, 185, 0.45);
  outline-offset: 1px;
}

/* ---------- 약관 모달 ---------- */
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
  z-index: 1000;
}

.modal {
  background: var(--color-background-soft);
  width: 100%;
  max-width: 520px;
  max-height: 80vh;
  border-radius: 14px;
  box-shadow: 0 18px 40px rgba(0, 0, 0, 0.18);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.modal-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  padding: 1rem 1.1rem;
  border-bottom: 1px solid var(--color-border);
}

.modal-title {
  margin: 0;
  font-size: 1.05rem;
  font-weight: 700;
  color: var(--color-heading);
  line-height: 1.35;
}

.modal-close {
  flex: 0 0 auto;
  width: 32px;
  height: 32px;
  border: none;
  background: transparent;
  color: var(--color-text);
  font-size: 1.5rem;
  line-height: 1;
  cursor: pointer;
  border-radius: 6px;
  transition: background 0.15s;
}

.modal-close:hover {
  background: rgba(0, 0, 0, 0.05);
}

.modal-body {
  flex: 1 1 auto;
  overflow-y: auto;
  padding: 1rem 1.1rem 1.2rem;
}

.modal-text {
  margin: 0;
  font: inherit;
  font-size: 0.9rem;
  line-height: 1.6;
  color: var(--color-text);
  white-space: pre-wrap;
  word-break: keep-all;
}

.modal-foot {
  padding: 0.75rem 1.1rem 1rem;
  border-top: 1px solid var(--color-border);
  display: flex;
  justify-content: flex-end;
}

.btn-modal-confirm {
  padding: 0.55rem 1.4rem;
  border-radius: 8px;
  border: none;
  background: var(--color-accent);
  color: #fff;
  font-weight: 600;
  font-size: 0.92rem;
  cursor: pointer;
  transition: filter 0.15s;
}

.btn-modal-confirm:hover {
  filter: brightness(1.05);
}
</style>
