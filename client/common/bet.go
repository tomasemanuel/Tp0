package common

import (
	"fmt"
	"strings"
)

type Bet struct {
	agency string
	first_name string
	last_name string
	document string
	birth_date string
	number string
}

func NewBet(agency string, first_name string, last_name string, document string, birth_date string, number string) *Bet {
	bet := &Bet{
		agency: agency,
		first_name: first_name,
		last_name: last_name,
		document: document,
		birth_date: birth_date,
		number: number,
	}
	return bet
}

func (b *Bet) Serialize() []byte {
	return []byte(fmt.Sprintf("%s|%s|%s|%s|%s|%s",
	b.agency, b.first_name, b.last_name, 
	b.document, b.birth_date, b.number))
}

func SerializeBatch(bets []*Bet) []byte {
	var lines []string
	for _, b := range bets {
		lines = append(lines, string(b.Serialize()))
	}
	return []byte(strings.Join(lines, "\n"))
}

