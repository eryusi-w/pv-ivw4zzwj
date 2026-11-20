---
name: youtube-channel-collector
description: "YouTube 채널 수집 대상을 추가하고 검증하는 작업을 자동화합니다."
---

# YouTube Channel Collector

YouTube 채널 수집 대상을 추가하고 검증하는 Opencode 스킬입니다.

## 사용 시점

- 새로운 YouTube 채널을 수집 대상에 추가할 때
- 채널 검증 및 중복 체크가 필요할 때
- 수집 스크립트 수정이 필요할 때

## 사용 방법

### 1. 채널 추가

```
@youtube-channel-collector add @채널이름
```

### 2. 채널 검증

```
@youtube-channel-collector verify @채널이름
```

### 3. 전체 목록 조회

```
@youtube-channel-collector list
```

## 프로젝트 연동

이 스킬은 GitHub_awesome_extractor 프로젝트의 다음 파일들을 수정합니다:

- `sources/manuagi_collector.py` - CHANNEL_HANDLES 리스트
- `config/settings.py` - YOUTUBE_CHANNEL_HANDLES 리스트

## 검증 규칙

추가 전 다음을 확인해야 합니다:
1. 채널이 AI/OSS 분야와 관련 있는가
2. 이미 목록에 존재하는가 (중복 방지)
3. YouTube API로 채널 ID 조회 가능한가
4. 활성화된 채널인가 (비활성 채널 제외)