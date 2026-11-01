FROM golang:1.25-alpine AS build
WORKDIR /src
COPY go.mod go.sum ./
RUN go mod download
COPY main.go ./
RUN CGO_ENABLED=0 GOOS=linux go build -trimpath -ldflags="-s -w" -o /out/fielddesk-agent .

FROM alpine:3.22 AS agent
LABEL org.fielddesk.lab.role="agent"
ENV LAB_ROLE=agent
COPY --from=build /out/fielddesk-agent /fielddesk-agent
USER 10001:10001
ENTRYPOINT ["/fielddesk-agent"]

FROM alpine:3.22 AS rogue
LABEL org.fielddesk.lab.role="rogue"
ENV LAB_ROLE=rogue
COPY --from=build /out/fielddesk-agent /fielddesk-agent
USER 10001:10001
ENTRYPOINT ["/fielddesk-agent"]
