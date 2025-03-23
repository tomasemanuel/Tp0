package common

import (
	"bufio"
	"fmt"
	"os"
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
func LoadBetsFromFile(path string, agencyID string) ([]*Bet, error) {
	file, err := os.Open(path)
	if err != nil {
		return nil, err
	}
	defer file.Close()

	var bets []*Bet
	scanner := bufio.NewScanner(file)
	for scanner.Scan() {
		line := scanner.Text()
		fields := strings.Split(line, ",")
		if len(fields) != 5 {
			continue
		}
		bets = append(bets, NewBet(
			agencyID,
			fields[0], fields[1], fields[2], fields[3], fields[4],
		))
	}
	return bets, nil
}
