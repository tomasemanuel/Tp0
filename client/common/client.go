package common

import (
	"bufio"
	"fmt"
	"net"
	"time"

	"github.com/op/go-logging"
)

var log = logging.MustGetLogger("log")

// ClientConfig Configuration used by the client
type ClientConfig struct {
	ID            string
	ServerAddress string
	LoopAmount    int
	LoopPeriod    time.Duration
}

// Client Entity that encapsulates how
type Client struct {
	config ClientConfig
	conn   net.Conn
}

// NewClient Initializes a new client receiving the configuration
// as a parameter
func NewClient(config ClientConfig) *Client {
	client := &Client{
		config: config,
	}
	return client
}

// CreateClientSocket Initializes client socket. In case of
// failure, error is printed in stdout/stderr and exit 1
// is returned
func (c *Client) createClientSocket() error {
	conn, err := net.Dial("tcp", c.config.ServerAddress)
	if err != nil {
		log.Criticalf(
			"action: connect | result: fail | client_id: %v | error: %v",
			c.config.ID,
			err,
		)
	}
	c.conn = conn
	return nil
}

// StartClientLoop Send messages to the client until some time threshold is met
func (c *Client) StartClientLoop() {

	// Create a context that can be canceled when receiving a termination signal
	ctx, cancel := context.WithCancel(context.Background())

	// Channel to capture OS signals
	sigChan := make(chan os.Signal, 1)

	// Notify the channel on SIGTERM or SIGINT
	signal.Notify(sigChan, syscall.SIGTERM, syscall.SIGINT)

	// Goroutine that waits for a termination signal and cancels the context
	go func() {
		sig := <-sigChan
		log.Infof("action: shutdown_signal_received | signal: %v | client_id: %v", sig, c.config.ID)
		cancel()
	}()
	
	// There is an autoincremental msgID to identify every message sent Messages if the message amount 
	/// threshold has not been surpassed
	for msgID := 1; msgID <= c.config.LoopAmount; msgID++ {

		// Check if shutdown signal was received
		select {
		case <-ctx.Done():
			log.Infof("action: graceful_exit | result: success | client_id: %v", c.config.ID)
			return
		default:
			// Create the connection to the server in every loop iteration
			err := c.createClientSocket()
			if err != nil {
				log.Errorf("action: connect | result: fail | client_id: %v | error: %v", c.config.ID, err)
				return
			}

			// TODO: Modify the send to avoid short-write
			// Send the message to the server
			fmt.Fprintf(
				c.conn,
				"[CLIENT %v] Message N°%v\n",
				c.config.ID,
				msgID,
			)

			// Read the response from the server
			msg, err := bufio.NewReader(c.conn).ReadString('\n')
			c.conn.Close()

			if err != nil {
				log.Errorf("action: receive_message | result: fail | client_id: %v | error: %v",
					c.config.ID,
					err,
				)
				return
			}

			// Log the successful response
			log.Infof("action: receive_message | result: success | client_id: %v | msg: %v",
				c.config.ID,
				msg,
			)

			// Wait a time between sending one message and the next one
			time.Sleep(c.config.LoopPeriod)
		}
	}

	// Log when the loop ends normally
	log.Infof("action: loop_finished | result: success | client_id: %v", c.config.ID)
}